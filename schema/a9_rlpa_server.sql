-- 🔀 rlpa-server schema
CREATE TABLE routes(id INTEGER PRIMARY KEY, host TEXT, path TEXT DEFAULT '/', upstream TEXT, auth TEXT DEFAULT 'none', rate_limit INTEGER DEFAULT 100, rate_window INTEGER DEFAULT 60, created_at DATETIME);
CREATE TABLE access_logs(id INTEGER PRIMARY KEY, route_id INTEGER REFERENCES routes(id), user TEXT, method TEXT, path TEXT, status INTEGER DEFAULT 0, ms INTEGER DEFAULT 0, ip TEXT, at DATETIME);
CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, api_key TEXT, is_admin INTEGER DEFAULT 0);
