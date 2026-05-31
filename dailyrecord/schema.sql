/* No local init - for now the local db is the source of truth */

CREATE TABLE track (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ua TEXT,
    device TEXT,
    os TEXT,
    browser TEXT,
    referer TEXT,
    url TEXT,
    blocked TEXT,
    request_date TEXT
);
