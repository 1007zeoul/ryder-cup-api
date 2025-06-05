CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    format TEXT,
    total_rounds INTEGER,
    current_round INTEGER DEFAULT 1,
    status TEXT DEFAULT 'inactive'
);

CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tournament_id INTEGER REFERENCES tournaments(id)
);

CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id),
    hole INTEGER NOT NULL,
    player1 TEXT NOT NULL,
    score1 INTEGER NOT NULL,
    player2 TEXT NOT NULL,
    score2 INTEGER NOT NULL
);

