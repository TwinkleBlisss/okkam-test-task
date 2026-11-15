CREATE TABLE IF NOT EXISTS statistics (
    id SERIAL PRIMARY KEY,
    date DATE,
    respondent INTEGER,
    sex INTEGER,
    age INTEGER,
    weight NUMERIC(15, 10)
);
