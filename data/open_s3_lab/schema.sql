-- Schema for Open S3 Bucket lab (SQLite)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS buckets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    region TEXT,
    owner TEXT,
    is_public INTEGER NOT NULL DEFAULT 0,
    policy TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_buckets_name ON buckets(name);

CREATE TABLE IF NOT EXISTS objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_id INTEGER NOT NULL REFERENCES buckets(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    size_bytes INTEGER,
    content_type TEXT,
    last_modified TEXT,
    storage_class TEXT,
    acl TEXT,
    public_url TEXT
);
CREATE INDEX IF NOT EXISTS idx_objects_bucket ON objects(bucket_id);
CREATE INDEX IF NOT EXISTS idx_objects_key ON objects(key);

CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_id INTEGER REFERENCES buckets(id),
    object_id INTEGER REFERENCES objects(id),
    timestamp TEXT NOT NULL,
    requester_ip TEXT,
    requester_agent TEXT,
    requester_identity TEXT,
    operation TEXT NOT NULL,
    status_code INTEGER,
    bytes_sent INTEGER,
    referrer TEXT
);
CREATE INDEX IF NOT EXISTS idx_logs_time ON access_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_ip ON access_logs(requester_ip);

CREATE TABLE IF NOT EXISTS fake_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    access_key TEXT UNIQUE,
    secret_key TEXT,
    created_for TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_id INTEGER REFERENCES buckets(id),
    object_id INTEGER REFERENCES objects(id),
    title TEXT,
    description TEXT,
    severity TEXT,
    reported_at TEXT,
    resolved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS attack_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    pattern TEXT NOT NULL,
    hint TEXT,
    example TEXT,
    level TEXT,
    category TEXT,
    description TEXT,
    expected_output TEXT
);

CREATE TABLE IF NOT EXISTS defense_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    pattern TEXT NOT NULL,
    hint TEXT,
    example TEXT,
    level TEXT,
    category TEXT,
    description TEXT,
    expected_output TEXT
);

CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_lab_id TEXT,
    timestamp TEXT,
    mode TEXT,
    command TEXT,
    outcome TEXT,
    details TEXT
);

CREATE TABLE IF NOT EXISTS attack_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_lab_id TEXT,
    timestamp TEXT,
    command TEXT,
    status TEXT,
    result TEXT
);

CREATE TABLE IF NOT EXISTS defense_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_lab_id TEXT,
    timestamp TEXT,
    command TEXT,
    status TEXT,
    result TEXT
);
