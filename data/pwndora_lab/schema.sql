-- Schema for PwnDora Challenge lab (SQLite)
-- Web application vulnerability lab with synthetic data

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_public INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    actor_id INTEGER,
    details TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS database_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    data TEXT NOT NULL,
    is_sensitive INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attack_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    pattern TEXT,
    hint TEXT,
    example TEXT,
    level TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS defense_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    pattern TEXT,
    hint TEXT,
    example TEXT,
    level TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS attack_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_lab_id TEXT,
    timestamp TEXT,
    command TEXT,
    outcome TEXT,
    details TEXT
);

CREATE TABLE IF NOT EXISTS defense_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_lab_id TEXT,
    timestamp TEXT,
    command TEXT,
    outcome TEXT,
    details TEXT
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

CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    detection_modifier REAL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS command_level_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_type TEXT,
    command_id INTEGER,
    level_name TEXT
);
