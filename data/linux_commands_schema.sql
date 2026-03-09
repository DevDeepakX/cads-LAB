-- Linux Commands Database Schema
-- Intermediate-level commands for practice across all labs

CREATE TABLE IF NOT EXISTS linux_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    pattern TEXT NOT NULL,
    description TEXT,
    example TEXT,
    level TEXT,
    use_case TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS command_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_id INTEGER,
    alias_name TEXT,
    FOREIGN KEY(command_id) REFERENCES linux_commands(id)
);

CREATE TABLE IF NOT EXISTS command_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_id INTEGER,
    execution_count INTEGER DEFAULT 0,
    last_used TEXT,
    FOREIGN KEY(command_id) REFERENCES linux_commands(id)
);
