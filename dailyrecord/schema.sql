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

CREATE TABLE blocklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value TEXT,
    block_type TEXT,  -- 'ua_agent', 'ua_string', 'path'
    added_date TEXT,
    UNIQUE(value, block_type)
);
INSERT INTO blocklist(value, block_type, added_date) VALUES('ClaudeBot', 'ua_agent', '2026-06-25');
INSERT INTO blocklist(value, block_type, added_date) VALUES('wp-admin', 'ua_string', '2026-06-25');
INSERT INTO blocklist(value, block_type, added_date) VALUES('wp-admin', 'path', '2026-06-25');
