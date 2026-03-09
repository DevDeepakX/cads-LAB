#!/usr/bin/env python3
"""Seed script for PwnDora Challenge lab.

Creates an SQLite DB at `pwndora_lab.db`, populates tables with synthetic
web application data, including vulnerable users, posts, and sessions.
All data is completely fictional and for educational purposes only.
"""
from __future__ import annotations
import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta


BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "pwndora_lab.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")


def now_iso(delta_days=0):
    return (datetime.now(timezone.utc) - timedelta(days=delta_days)).isoformat()


def load_schema(conn: sqlite3.Connection):
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def insert_many(conn, sql, rows):
    cur = conn.cursor()
    cur.executemany(sql, rows)
    return cur


def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    load_schema(conn)

    # Levels
    levels = [
        ("Beginner", 0.3, "Slower/lenient AI detection, hints more helpful"),
        ("Intermediate", 0.6, "Moderate AI detection and reactive behavior"),
        ("Advanced", 0.85, "Aggressive AI detection and active mitigation"),
    ]
    insert_many(conn, "INSERT INTO levels(name,detection_modifier,description) VALUES (?,?,?)", levels)

    # Users: completely fictional, dummy data
    users = [
        ("admin", "admin@pwndora-lab.local", "5f4dcc3b5aa765d61d8327deb882cf99", "admin", 1, now_iso(180)),
        ("alice", "alice@pwndora-lab.local", "e99a18c428cb38d5f260853678922e03", "user", 1, now_iso(60)),
        ("bob", "bob@pwndora-lab.local", "25f9e7d3fba6b6a893d40faea47147a5", "user", 1, now_iso(45)),
        ("charlie", "charlie@pwndora-lab.local", "5f4dcc3b5aa765d61d8327deb882cf99", "user", 1, now_iso(30)),
        ("davinder", "davinder@pwndora-lab.local", "0cbc6611f5540bd0809a388dc95a615b", "moderator", 1, now_iso(15)),
    ]
    insert_many(conn, "INSERT INTO users(username,email,password_hash,role,is_active,created_at) VALUES (?,?,?,?,?,?)", users)

    # Fetch user ids
    cur = conn.cursor()
    cur.execute("SELECT id,username FROM users")
    user_map = {r[1]: r[0] for r in cur.fetchall()}

    # Posts
    posts_rows = []
    posts_data = [
        (user_map["alice"], "Welcome to PwnDora", "This is my first post on the lab platform. Excited to learn!", 1, now_iso(50)),
        (user_map["bob"], "SQL Injection Tips", "Always remember to validate input. That's the key!", 1, now_iso(40)),
        (user_map["charlie"], "Secret Admin Panel", "Found the admin panel at /admin.php. Check it out!", 0, now_iso(20)),
        (user_map["davinder"], "Security Best Practices", "Use prepared statements and parameterized queries.", 1, now_iso(10)),
        (user_map["admin"], "Lab Announcement", "Welcome all! This is a safe training environment.", 1, now_iso(5)),
    ]
    insert_many(conn, "INSERT INTO posts(user_id,title,content,is_public,created_at) VALUES (?,?,?,?,?)", posts_data)

    # Fetch post ids
    cur.execute("SELECT id FROM posts ORDER BY id")
    post_ids = [r[0] for r in cur.fetchall()]

    # Comments
    comments_data = [
        (post_ids[0], user_map["bob"], "Nice first post!", now_iso(48)),
        (post_ids[1], user_map["alice"], "Great tip, thanks!", now_iso(35)),
        (post_ids[1], user_map["charlie"], "I never knew that.", now_iso(32)),
        (post_ids[3], user_map["bob"], "Completely agree!", now_iso(8)),
    ]
    insert_many(conn, "INSERT INTO comments(post_id,user_id,content,created_at) VALUES (?,?,?,?)", comments_data)

    # Sessions: fictional, expired, and active
    sessions_data = [
        (user_map["admin"], "sess_admin_old_12345", "203.0.113.5", "Mozilla/5.0", now_iso(100), now_iso(95)),
        (user_map["alice"], "sess_alice_active_6789", "198.51.100.10", "Chrome/90", now_iso(2), now_iso(32)),
        (user_map["bob"], "sess_bob_active_5432", "192.0.2.20", "Firefox/88", now_iso(1), now_iso(31)),
    ]
    insert_many(conn, "INSERT INTO sessions(user_id,session_token,ip_address,user_agent,created_at,expires_at) VALUES (?,?,?,?,?,?)", sessions_data)

    # Admin logs
    admin_logs_data = [
        ("user_created", user_map["admin"], "Created user: charlie", now_iso(30)),
        ("user_updated", user_map["admin"], "Updated user: bob", now_iso(25)),
        ("post_flagged", user_map["davinder"], "Flagged post 3 as inappropriate", now_iso(15)),
        ("user_deleted", user_map["admin"], "Deleted user: inactive_user", now_iso(10)),
    ]
    insert_many(conn, "INSERT INTO admin_logs(action,actor_id,details,timestamp) VALUES (?,?,?,?)", admin_logs_data)

    # Database records (sensitive data stored insecurely for lab)
    db_records = [
        ("credit_card", "4532-XXXX-XXXX-1234", 1, now_iso(60)),
        ("api_key", "sk_live_abcdef123456", 1, now_iso(50)),
        ("config", "database_url=mysql://root:password@localhost/pwndora", 1, now_iso(40)),
        ("log_entry", "User admin logged in from 192.168.1.1", 0, now_iso(1)),
    ]
    insert_many(conn, "INSERT INTO database_records(record_type,data,is_sensitive,created_at) VALUES (?,?,?,?)", db_records)

    # Attack commands for PwnDora
    attack_cmds = [
        ("SQL Injection", "' OR '1'='1", "Test for SQL injection in login form", "username=' OR '1'='1", "Beginner", "injection"),
        ("XSS via Comment", "<script>alert('xss')</script>", "Inject script tags in post comments", "Comment: <img src=x onerror=alert('xss')>", "Intermediate", "xss"),
        ("Path Traversal", "../../../etc/passwd", "Attempt to access files outside web root", "POST /download?file=../../../etc/passwd", "Intermediate", "access"),
        ("Brute Force Login", "admin/password123", "Attempt multiple password combinations", "POST /login with user=admin&pass=password123", "Beginner", "auth"),
        ("CSRF Token Bypass", "Form without CSRF token", "Submit form without valid CSRF protection", "POST /delete_post without csrf_token", "Advanced", "csrf"),
        ("Insecure Deserialization", "unserialize() exploit", "Exploit unsafe object deserialization", "Send crafted serialized PHP object", "Advanced", "deserialization"),
    ]
    insert_many(conn, "INSERT INTO attack_commands(name,pattern,hint,example,level,category) VALUES (?,?,?,?,?,?)", attack_cmds)

    # Defense commands for PwnDora
    defense_cmds = [
        ("Input Validation", "validate_input()", "Implement strict input validation rules", "Use parameterized queries and whitelisting", "Beginner", "prevention"),
        ("Output Encoding", "htmlspecialchars()", "Encode user-supplied data in output", "Apply context-aware encoding (HTML, JS, URL)", "Beginner", "prevention"),
        ("CSRF Protection", "csrf_token", "Implement CSRF tokens on all state-changing forms", "Generate and validate unique tokens per session", "Intermediate", "prevention"),
        ("Session Management", "regenerate_session_id()", "Securely manage session identifiers", "Regenerate ID after login, set secure flags", "Intermediate", "remediation"),
        ("Rate Limiting", "implement_rate_limit()", "Limit failed login attempts", "Lock account after N failed attempts", "Intermediate", "detection"),
        ("Web Application Firewall", "WAF rules", "Deploy WAF to filter malicious requests", "Block known attack patterns and payloads", "Advanced", "remediation"),
    ]
    insert_many(conn, "INSERT INTO defense_commands(name,pattern,hint,example,level,category) VALUES (?,?,?,?,?,?)", defense_cmds)

    conn.commit()
    conn.close()
    print(f"PwnDora lab database seeded successfully at {DB_PATH}")


if __name__ == "__main__":
    seed()
