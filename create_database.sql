-- Create Movies Table
CREATE TABLE IF NOT EXISTS Movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    release_date INTEGER,
    director_id INTEGER,
    avg_rating REAL DEFAULT 0,
    FOREIGN KEY (director_id) REFERENCES Directors(director_id)
);

-- Create Users Table
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY,
    user_name TEXT NOT NULL,
    password TEXT NOT NULL
);

-- Create Reviews Table
CREATE TABLE IF NOT EXISTS Reviews (
    movie_id INTEGER,
    user_id INTEGER,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    review_text TEXT,
    PRIMARY KEY (movie_id, user_id),
    FOREIGN KEY (movie_id) REFERENCES Movies(movie_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Create Genres Table
CREATE TABLE IF NOT EXISTS Genres (
    genre_id INTEGER PRIMARY KEY,
    genre_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS MovieGenres (
    movie_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES Movies (movie_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES Genres (genre_id) ON DELETE CASCADE
);

-- Create Actors Table
CREATE TABLE IF NOT EXISTS Actors (
    actor_id INTEGER PRIMARY KEY,
    actor_name TEXT NOT NULL
);

-- Create MovieActors Table
CREATE TABLE IF NOT EXISTS MovieActors (
    movie_id INTEGER,
    actor_id INTEGER,
    PRIMARY KEY (movie_id, actor_id),
    FOREIGN KEY (movie_id) REFERENCES Movies(movie_id),
    FOREIGN KEY (actor_id) REFERENCES Actors(actor_id)
);

-- Create Directors Table
CREATE TABLE IF NOT EXISTS Directors (
    director_id INTEGER PRIMARY KEY,
    director_name TEXT NOT NULL
);

-- Create Watchlists Table
CREATE TABLE IF NOT EXISTS Watchlists (
    user_id INTEGER,
    movie_id INTEGER,
    PRIMARY KEY (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (movie_id) REFERENCES Movies(movie_id)
);