-- Schema for Network Reconnaissance lab (SQLite)
-- Network environment simulation with hosts, services, and vulnerability data

CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    hostname TEXT,
    os_type TEXT,
    is_active INTEGER DEFAULT 1,
    discovered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT,
    service_name TEXT,
    version TEXT,
    is_vulnerable INTEGER DEFAULT 0,
    discovered_at TEXT NOT NULL,
    FOREIGN KEY(host_id) REFERENCES hosts(id),
    UNIQUE(host_id, port, protocol)
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    cve_id TEXT,
    title TEXT,
    severity TEXT,
    description TEXT,
    impact TEXT,
    remediation TEXT,
    discovered_at TEXT NOT NULL,
    FOREIGN KEY(service_id) REFERENCES services(id)
);

CREATE TABLE IF NOT EXISTS network_traffic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_ip TEXT NOT NULL,
    dst_ip TEXT NOT NULL,
    dst_port INTEGER,
    protocol TEXT,
    packet_count INTEGER,
    bytes_sent INTEGER,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS firewall_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT UNIQUE NOT NULL,
    src_range TEXT,
    dst_range TEXT,
    dst_port INTEGER,
    protocol TEXT,
    action TEXT,
    is_enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ids_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_ip TEXT NOT NULL,
    dst_ip TEXT NOT NULL,
    alert_type TEXT,
    severity TEXT,
    details TEXT,
    timestamp TEXT NOT NULL
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
