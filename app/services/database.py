import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "database.db"


def get_database_url(db_url: str | None = None) -> str:
    if db_url:
        return db_url
    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")


def _db_path_from_url(db_url: str) -> str:
    """Convert SQLAlchemy-like sqlite URLs into a filesystem path for local SQLite use."""
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "", 1)
    if db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "", 1)
    return str(DEFAULT_DB_PATH)


def get_db_connection(db_url: str | None = None):
    url = get_database_url(db_url)
    db_path = _db_path_from_url(url)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_column(conn, table, column, definition):
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def initialize_database(db_url: str | None = None):
    """Create the core schema for the foundation layer used by CADS."""
    conn = get_db_connection(db_url)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'student',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_column(conn, "users", "updated_at", "TEXT")
    _ensure_column(conn, "users", "is_active", "INTEGER DEFAULT 1")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'Cloud Security',
            difficulty TEXT DEFAULT 'Beginner',
            xp INTEGER DEFAULT 100,
            status TEXT DEFAULT 'draft',
            metadata TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for column, definition in {
        "slug": "TEXT", "lab_id": "TEXT", "title": "TEXT", "description": "TEXT",
        "category": "TEXT DEFAULT 'Cloud Security'", "difficulty": "TEXT DEFAULT 'Beginner'",
        "xp": "INTEGER DEFAULT 100", "status": "TEXT DEFAULT 'draft'",
        "metadata": "TEXT DEFAULT '{}'", "updated_at": "TEXT",
    }.items():
        _ensure_column(conn, "labs", column, definition)

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lab_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            user_id INTEGER,
            lab_id INTEGER,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            status TEXT DEFAULT 'NOT_STARTED',
            score INTEGER DEFAULT 0,
            hints_used INTEGER DEFAULT 0,
            commands_executed INTEGER DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (lab_id) REFERENCES labs(id)
        )
        """
    )
    _ensure_column(conn, "lab_sessions", "last_activity_at", "TEXT")
    _ensure_column(conn, "lab_sessions", "time_spent_seconds", "INTEGER DEFAULT 0")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lab_objectives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER,
            objective_key TEXT,
            objective_text TEXT,
            objective_type TEXT DEFAULT 'attack',
            rank_order INTEGER DEFAULT 1,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lab_id) REFERENCES labs(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cloud_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            resource_type TEXT,
            resource_name TEXT,
            region TEXT DEFAULT 'ap-south-1',
            configuration TEXT DEFAULT '{}',
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES lab_sessions(session_id)
        )
        """
    )
    _ensure_column(conn, "cloud_resources", "state", "TEXT DEFAULT '{}'")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cloud_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            service TEXT,
            event_name TEXT,
            actor TEXT,
            resource_id INTEGER,
            resource_type TEXT,
            source_ip TEXT,
            region TEXT DEFAULT 'ap-south-1',
            outcome TEXT DEFAULT 'SUCCESS',
            severity TEXT DEFAULT 'MEDIUM',
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (session_id) REFERENCES lab_sessions(session_id)
        )
        """
    )
    _ensure_column(conn, "cloud_events", "event_id", "TEXT")
    _ensure_column(conn, "cloud_events", "resource_name", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            title TEXT,
            severity TEXT DEFAULT 'MEDIUM',
            status TEXT DEFAULT 'OPEN',
            source TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for column, definition in {
        "finding_id": "TEXT", "rule_id": "TEXT", "service": "TEXT",
        "resource_id": "TEXT", "evidence": "TEXT DEFAULT '[]'",
        "recommendation": "TEXT", "first_seen": "TEXT", "last_seen": "TEXT",
        "updated_at": "TEXT",
    }.items():
        _ensure_column(conn, "findings", column, definition)

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS objective_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            objective_id TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            completed_at TEXT,
            evidence TEXT DEFAULT '{}',
            UNIQUE(session_id, objective_id),
            FOREIGN KEY (session_id) REFERENCES lab_sessions(session_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS score_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (session_id) REFERENCES lab_sessions(session_id)
        )
        """
    )
    cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    migration_count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    if migration_count == 0:
        conn.execute("INSERT INTO schema_migrations (version) VALUES ('000_baseline_unversioned')")
    conn.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('001_phase5_persistence')")
    conn.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('002_phase6_runtime_stability')")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            flag_value TEXT,
            flag_type TEXT DEFAULT 'final',
            is_found INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER,
            hint_key TEXT,
            hint_text TEXT,
            level INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lab_id) REFERENCES labs(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hint_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            hint_id INTEGER,
            used_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hint_id) REFERENCES hints(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            submission_type TEXT,
            payload TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            lab_id INTEGER,
            score INTEGER DEFAULT 0,
            xp_awarded INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (lab_id) REFERENCES labs(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            lab_id INTEGER,
            status TEXT DEFAULT 'NOT_STARTED',
            progress_percent INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (lab_id) REFERENCES labs(id)
        )
        """
    )

    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_labs_slug ON labs(slug)")
    except sqlite3.OperationalError:
        pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON lab_sessions(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_lab ON lab_sessions(lab_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON cloud_events(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_resources_session ON cloud_resources(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_session ON scores(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_resources_session_name ON cloud_resources(session_id, resource_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session_time ON cloud_events(session_id, timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_session_status ON findings(session_id, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_objectives_session ON objective_progress(session_id)")

    conn.commit()
    conn.close()
    return _db_path_from_url(get_database_url(db_url))
