import sqlite3
import requests

OMDB_API_KEY = ""

def connect_db():
    return sqlite3.connect('movie_streaming.db')

def create_tables(conn):
    with open("create_database.sql", 'r') as file:
        sql_script = file.read()
        with conn:
            conn.executescript(sql_script)
    print("Tables created from SQL file successfully.")

def get_username_by_id(conn, user_id):
    cursor = conn.execute("SELECT user_name FROM Users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    return user[0] if user else None

def fetch_movie_data(title):
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            return data
        else:
            print(f"Error: {data.get('Error')}")
            return None
    else:
        print(f"Failed to fetch data from OMDb API. Status Code: {response.status_code}")
        return None

def check_duplicate_movie(conn, title):
    cursor = conn.execute("SELECT movie_id FROM Movies WHERE title = ?", (title,))
    return cursor.fetchone() is not None

def add_movie_to_db(conn, data):
    title = data.get("Title")
    
    if check_duplicate_movie(conn, title):
        print(f"Movie '{title}' already exists in the database.")
        return

    with conn:
        director_name = data.get("Director", "Unknown")
        cursor = conn.execute("SELECT director_id FROM Directors WHERE director_name = ?", (director_name,))
        director_row = cursor.fetchone()
        if director_row:
            director_id = director_row[0]
        else:
            conn.execute("INSERT INTO Directors (director_name) VALUES (?)", (director_name,))
            director_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        release_date = data.get("Released")
        cursor = conn.execute(
            "INSERT INTO Movies (title, release_date, director_id) VALUES (?, ?, ?)", 
            (title, release_date, director_id)
        )
        movie_id = cursor.lastrowid

        genres = data.get("Genre", "").split(", ")
        for genre in genres:
            genre = genre.strip()
            cursor = conn.execute("SELECT genre_id FROM Genres WHERE genre_name = ?", (genre,))
            genre_row = cursor.fetchone()
            if genre_row:
                genre_id = genre_row[0]
            else:
                conn.execute("INSERT INTO Genres (genre_name) VALUES (?)", (genre,))
                genre_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            conn.execute("INSERT INTO MovieGenres (movie_id, genre_id) VALUES (?, ?)", (movie_id, genre_id))

        actors = data.get("Actors", "").split(", ")
        for actor in actors:
            actor = actor.strip()
            cursor = conn.execute("SELECT actor_id FROM Actors WHERE actor_name = ?", (actor,))
            actor_row = cursor.fetchone()
            if actor_row:
                actor_id = actor_row[0]
            else:
                conn.execute("INSERT INTO Actors (actor_name) VALUES (?)", (actor,))
                actor_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            conn.execute("INSERT INTO MovieActors (movie_id, actor_id) VALUES (?, ?)", (movie_id, actor_id))

        print(f"Movie '{title}' added to the database with genres: {', '.join(genres)}.")

def create_user(conn, username, password):
    cursor = conn.execute("SELECT user_id FROM Users WHERE user_name = ?", (username,))
    if cursor.fetchone():
        print("Username already exists. Try a different one.")
        return False
    
    with conn:
        conn.execute("INSERT INTO Users (user_name, password) VALUES (?, ?)", (username, password))
    print(f"User '{username}' created successfully.")
    return True

def authenticate_user(conn, username, password):
    cursor = conn.execute("SELECT user_id FROM Users WHERE user_name = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    if user:
        print(f"Welcome, {username}!")
        return user[0]  # Return user_id
    else:
        print("Invalid username or password.")
        return None

def user_login(conn):
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    user_id = authenticate_user(conn, username, password)
    if user_id:
        print(f"Logged in as {username}")
    return user_id

def user_signup(conn):
    username = input("Enter a username: ")
    password = input("Enter a password: ")
    if create_user(conn, username, password):
        cursor = conn.execute("SELECT user_id FROM Users WHERE user_name = ?", (username,))
        return cursor.fetchone()[0]  # Return user_id
    else:
        return None

def add_to_watchlist(conn, user_id, movie_id):
    with conn:
        conn.execute("INSERT INTO Watchlists (user_id, movie_id) VALUES (?, ?)", (user_id, movie_id))
    print("Movie added to your watchlist.")

def remove_from_watchlist(conn, user_id, movie_id):
    with conn:
        conn.execute("DELETE FROM Watchlists WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
    print("Movie removed from your watchlist.")

def leave_review(conn, user_id, movie_id, rating, review_text):
    if not (1 <= rating <= 5):
        print("Rating must be between 1 and 5 stars.")
        return
    
    with conn:
        cursor = conn.execute("SELECT * FROM Reviews WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
        review_exists = cursor.fetchone()

        if review_exists:
            conn.execute(
                "UPDATE Reviews SET rating = ?, review_text = ? WHERE user_id = ? AND movie_id = ?",
                (rating, review_text, user_id, movie_id)
            )
            print("Review updated.")
        else:
            conn.execute(
                "INSERT INTO Reviews (user_id, movie_id, rating, review_text) VALUES (?, ?, ?, ?)",
                (user_id, movie_id, rating, review_text)
            )
            print("Review added.")

        cursor = conn.execute("SELECT AVG(rating) FROM Reviews WHERE movie_id = ?", (movie_id,))
        avg_rating = cursor.fetchone()[0]
        conn.execute("UPDATE Movies SET avg_rating = ? WHERE movie_id = ?", (avg_rating, movie_id))
        print(f"Movie's average rating updated to {avg_rating:.2f}.")

def search_movies_by_director(conn):
    director_name = input("Enter director's name: ").strip()
    cursor = conn.execute("""
        SELECT Movies.title, Movies.release_date, Directors.director_name, Movies.avg_rating, 
               GROUP_CONCAT(Genres.genre_name, ', ') AS genres
        FROM Movies
        JOIN Directors ON Movies.director_id = Directors.director_id
        LEFT JOIN MovieGenres ON Movies.movie_id = MovieGenres.movie_id
        LEFT JOIN Genres ON MovieGenres.genre_id = Genres.genre_id
        WHERE LOWER(Directors.director_name) = LOWER(?)
        GROUP BY Movies.movie_id
    """, (director_name,))
    movies = cursor.fetchall()
    if movies:
        print(f"Movies by director '{director_name}':")
        print(f"{'Title':<30}{'Release Date':<15}{'Director Name':<35}{'Avg Rating':<12}{'Genres':<35}")
        print("-" * 110)
        for movie in movies:
            print(f"{movie[0]:<30}{movie[1]:<15}{movie[2]:<35}{movie[3]:<12.2f}{movie[4]:<35}")
    else:
        print(f"No movies found by director '{director_name}'.")

def search_movies_by_actor(conn):
    actor_name = input("Enter actor's name: ").strip()
    cursor = conn.execute("""
        SELECT Movies.title, Movies.release_date, Directors.director_name, Movies.avg_rating, 
               GROUP_CONCAT(Genres.genre_name, ', ') AS genres
        FROM Movies
        JOIN Directors ON Movies.director_id = Directors.director_id
        JOIN MovieActors ON Movies.movie_id = MovieActors.movie_id
        JOIN Actors ON MovieActors.actor_id = Actors.actor_id
        LEFT JOIN MovieGenres ON Movies.movie_id = MovieGenres.movie_id
        LEFT JOIN Genres ON MovieGenres.genre_id = Genres.genre_id
        WHERE LOWER(Actors.actor_name) = LOWER(?)
        GROUP BY Movies.movie_id
    """, (actor_name,))
    movies = cursor.fetchall()
    if movies:
        print(f"Movies with actor '{actor_name}':")
        print(f"{'Title':<30}{'Release Date':<15}{'Director Name':<35}{'Avg Rating':<12}{'Genres':<35}")
        print("-" * 120)
        for movie in movies:
            print(f"{movie[0]:<30}{movie[1]:<15}{movie[2]:<35}{movie[3]:<12.2f}{movie[4]:<35}")
    else:
        print(f"No movies found with actor '{actor_name}'.")

def view_all_movies(conn):
    cursor = conn.execute("""
        SELECT m.title, m.release_date, d.director_name, m.avg_rating, 
               GROUP_CONCAT(g.genre_name, ', ') AS genres
        FROM Movies m
        JOIN Directors d ON m.director_id = d.director_id
        LEFT JOIN MovieGenres mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.genre_id
        GROUP BY m.movie_id
    """)
    movies = cursor.fetchall()
    print(f"{'Title':<30}{'Release Date':<15}{'Director Name':<35}{'Avg Rating':<12}{'Genres':<35}{'Actors':<40}")
    print("-" * 180)
    for movie in movies:
        movie_title = movie[0]
        cursor_actors = conn.execute("""
            SELECT a.actor_name
            FROM Actors a
            JOIN MovieActors ma ON a.actor_id = ma.actor_id
            JOIN Movies m ON ma.movie_id = m.movie_id
            WHERE m.title = ?
        """, (movie_title,))
        actors = cursor_actors.fetchall()
        actor_names = [actor[0] for actor in actors]

        # Display the movie details and actors
        print(f"{movie[0]:<30}{movie[1]:<15}{movie[2]:<35}{movie[3]:<12.2f}{movie[4]:<35}{', '.join(actor_names):<40}")

def view_movies_by_genre(conn):
    genre = input("Enter genre: ").strip()
    cursor = conn.execute("""
        SELECT m.title, m.release_date, d.director_name, m.avg_rating, 
               GROUP_CONCAT(g.genre_name, ', ') AS genres
        FROM Movies m
        JOIN Directors d ON m.director_id = d.director_id
        JOIN MovieGenres mg ON m.movie_id = mg.movie_id
        JOIN Genres g ON mg.genre_id = g.genre_id
        WHERE g.genre_name = ?
        GROUP BY m.movie_id
    """, (genre,))
    movies = cursor.fetchall()
    if movies:
        print(f"Movies in genre '{genre}':")
        print(f"{'Title':<30}{'Release Date':<15}{'Director Name':<35}{'Avg Rating':<12}{'Genres':<35}")
        print("-" * 110)
        for movie in movies:
            print(f"{movie[0]:<30}{movie[1]:<15}{movie[2]:<35}{movie[3]:<12.2f}{movie[4]:<35}")
    else:
        print(f"No movies found in genre '{genre}'.")

def view_top_rated_movies(conn):
    cursor = conn.execute("""
        SELECT Movies.title, AVG(Reviews.rating) AS avg_rating
        FROM Reviews
        JOIN Movies ON Reviews.movie_id = Movies.movie_id
        GROUP BY Movies.movie_id
        ORDER BY avg_rating DESC
        LIMIT 5
    """)
    movies = cursor.fetchall()
    print("Top 5 Most Rated Movies:")
    for movie in movies:
        print(f"{movie[0]} - Average Rating: {movie[1]}")

def user_watchlist(conn, user_id):
    while True:
        print("\n1. View Movies in Watchlist")
        print("2. Add Movie to Watchlist")
        print("3. Remove Movie from Watchlist")
        print("4. Back to Main Menu")
        choice = input("Choose an option: ")
        if choice == "1":
            cursor = conn.execute("SELECT Movies.title FROM Movies JOIN Watchlists ON Movies.movie_id = Watchlists.movie_id WHERE Watchlists.user_id = ?", (user_id,))
            movies = cursor.fetchall()
            print("Movies in your Watchlist:")
            for movie in movies:
                print(movie[0])
        elif choice == "2":
            movie_title = input("Enter the movie title to add to your watchlist: ")
            cursor = conn.execute("SELECT movie_id FROM Movies WHERE title = ?", (movie_title,))
            movie = cursor.fetchone()
            if movie:
                conn.execute("INSERT INTO Watchlists (user_id, movie_id) VALUES (?, ?)", (user_id, movie[0]))
                print(f"Movie '{movie_title}' added to your watchlist.")
            else:
                print("Movie not found.")
        elif choice == "3":
            movie_title = input("Enter the movie title to remove from your watchlist: ")
            cursor = conn.execute("SELECT movie_id FROM Movies WHERE title = ?", (movie_title,))
            movie = cursor.fetchone()
            if movie:
                conn.execute("DELETE FROM Watchlists WHERE user_id = ? AND movie_id = ?", (user_id, movie[0]))
                print(f"Movie '{movie_title}' removed from your watchlist.")
            else:
                print("Movie not found.")
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

def user_reviews(conn, current_user_id):
    while True:
        print("\n1. View Reviews on a Movie")
        print("2. Leave a Review on a Movie")
        print("3. Back to Main Menu")
        choice = input("Choose an option: ")
        if choice == "1":
            movie_title = input("Enter the movie title: ")
            cursor = conn.execute("""
                SELECT Users.user_name, Reviews.rating, Reviews.review_text
                FROM Reviews
                JOIN Users ON Reviews.user_id = Users.user_id
                JOIN Movies ON Reviews.movie_id = Movies.movie_id
                WHERE LOWER(Movies.title) = LOWER(?)
            """, (movie_title,))
            reviews = cursor.fetchall()
            if reviews:
                print(f"Reviews for '{movie_title}':")
                for review in reviews:
                    print(f"{review[0]} rated {review[1]} stars: {review[2]}")
            else:
                print("No reviews for this movie.")
        elif choice == "2":
            movie_title = input("Enter the movie title: ")
            rating = input("Enter your rating (1-5): ")
            review_text = input("Enter your review: ")
            cursor = conn.execute("SELECT movie_id FROM Movies WHERE title = ?", (movie_title,))
            movie = cursor.fetchone()
            if movie:
                movie_id = movie[0]
                leave_review(conn, current_user_id, movie_id, int(rating), review_text)
            else:
                print("Movie not found.")
        elif choice == "3":
            break
        else:
            print("Invalid choice.")

def main():
    conn = connect_db()
    create_tables(conn)

    current_user_id = None

    while True:
        print("\n1. Login")
        print("2. Signup")
        print("3. View and Add Movie from OMDb API")
        print("4. View/Add/Remove Movie from Watchlist")
        print("5. View or Leave a Review")
        print("6. View Movies by Genre")
        print("7. View Top 5 Most Rated Movies")
        print("8. View Movies by Director/Actor")
        print("9. Exit")
        
        choice = input("Choose an option: ")

        if choice == "1":  # Login
            current_user_id = user_login(conn)
        elif choice == "2":  # Signup
            current_user_id = user_signup(conn)
        elif choice == "3":  # View and Add Movie from OMDb API
            print("\n1. View all movies in the database")
            print("2. Add a movie to the database")
            sub_choice = input("Choose an option: ")
            if sub_choice == "1":
                view_all_movies(conn)
            elif sub_choice == "2":
                movie_title = input("Enter movie title: ")
                movie_data = fetch_movie_data(movie_title)
                if movie_data:
                    add_movie_to_db(conn, movie_data)
        elif choice == "4":  # View/Add/Remove Movie from Watchlist
            if current_user_id:
                user_watchlist(conn, current_user_id)
            else:
                print("You must log in first.")
        elif choice == "5":  # View or Leave Review
            if current_user_id:
                user_reviews(conn, current_user_id)
            else:
                print("You must log in first.")
        elif choice == "6":  # View Movies by Genre
            view_movies_by_genre(conn)
        elif choice == "7":  # View Top 5 Most Rated Movies
            view_top_rated_movies(conn)
        elif choice == "8":  # View Top 5 Most Rated Movies
            print("\n1. View movies by director")
            print("2. View movies by actor")
            sub_choice = input("Choose an option: ")
            if sub_choice == "1":
                search_movies_by_director(conn)
            elif sub_choice == "2":
                search_movies_by_actor(conn)
        elif choice == "9":  # Exit
            break
        else:
            print("Invalid choice.")

main()
