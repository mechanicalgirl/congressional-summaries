/* No local init - for now the local db is the source of truth */

CREATE TABLE track (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ua TEXT,
    device TEXT,
    os TEXT,
    browser TEXT,
    is_bot TEXT,
    is_email_client TEXT,
    is_mobile TEXT,
    is_pc TEXT,
    is_tablet TEXT,
    is_touch_capable TEXT,
    request_date TEXT
);
