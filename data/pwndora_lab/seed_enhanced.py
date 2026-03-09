#!/usr/bin/env python3
"""Enhanced seed script for PwnDora Challenge lab with large dummy dataset."""
from __future__ import annotations
import sqlite3
import json
import os
import random
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
    random.seed(42)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    load_schema(conn)

    # ==================== LEVELS ====================
    levels = [
        ("Beginner", 0.3, "Slower AI detection, helpful hints"),
        ("Intermediate", 0.6, "Moderate AI detection and reactive behavior"),
        ("Advanced", 0.85, "Aggressive AI detection and active mitigation"),
    ]
    insert_many(conn, "INSERT INTO levels(name, detection_modifier, description) VALUES (?, ?, ?)", levels)

    # ==================== USERS ====================
    users = [
        ("admin", "admin@pwndora-lab.local", "5f4dcc3b5aa765d61d8327deb882cf99", "admin", 1, now_iso(180)),
        ("alice", "alice@pwndora-lab.local", "e99a18c428cb38d5f260853678922e03", "user", 1, now_iso(60)),
        ("bob", "bob@pwndora-lab.local", "25f9e7d3fba6b6a893d40faea47147a5", "user", 1, now_iso(45)),
        ("charlie", "charlie@pwndora-lab.local", "5f4dcc3b5aa765d61d8327deb882cf99", "user", 1, now_iso(30)),
        ("davinder", "davinder@pwndora-lab.local", "0cbc6611f5540bd0809a388dc95a615b", "moderator", 1, now_iso(15)),
        ("eva", "eva@pwndora-lab.local", "fcea920f7412b5da7be0cf42b8c93759", "user", 1, now_iso(25)),
        ("frank", "frank@pwndora-lab.local", "827ccb0eea8a706c4c34a16891f84e7b", "user", 0, now_iso(5)),
        ("grace", "grace@pwndora-lab.local", "6512bd43d9caa6e02c990b0a82652dca", "moderator", 1, now_iso(12)),
        ("henry", "henry@pwndora-lab.local", "0b4e3a6e5c1d9f2b8a3c4e6f7d8e9a0b", "user", 1, now_iso(20)),
        ("iris", "iris@pwndora-lab.local", "5ab557c937e38aca2fab08e86f2e9404", "user", 1, now_iso(18)),
    ]
    insert_many(conn, "INSERT INTO users(username, email, password_hash, role, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)", users)

    # Fetch user ids
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users")
    user_map = {r[1]: r[0] for r in cur.fetchall()}

    # ==================== POSTS (100+) ====================
    posts_rows = []
    post_titles = [
        "Welcome to PwnDora",
        "SQL Injection Tips",
        "Secret Admin Panel",
        "Security Best Practices",
        "Lab Announcement",
        "XSS Vulnerability Found",
        "CSRF Protection Missing",
        "Authentication Bypass",
        "Data Validation Matters",
        "Web Security Overview",
        "Debugging Techniques",
        "Performance Tips",
        "Database Optimization",
        "API Security",
        "Session Management",
    ]
    
    post_contents = [
        "This is my first post on the lab platform. Excited to learn!",
        "Always remember to validate input. That's the key!",
        "Found the admin panel at /admin.php. Check it out!",
        "Use prepared statements and parameterized queries.",
        "Welcome all! This is a safe training environment.",
        "Cross-site scripting is a common vulnerability.",
        "CSRF tokens are essential for form security.",
        "Never trust user input directly.",
        "Sanitize all output before rendering.",
        "Keep your framework updated.",
        "Use logging for security audits.",
        "Monitor application performance.",
        "Index your database queries.",
        "Implement rate limiting.",
        "Use HTTPS for all connections.",
    ]
    
    user_list = list(user_map.values())
    for i in range(100):
        title = post_titles[i % len(post_titles)] + f" #{i//len(post_titles) + 1}" if i >= len(post_titles) else post_titles[i]
        content = post_contents[i % len(post_contents)] + f"\n\nPost #{i+1} content with detailed information."
        user_id = random.choice(user_list)
        is_public = random.choice([0, 1])
        posts_rows.append((user_id, title, content, is_public, now_iso(i % 90)))
    
    insert_many(conn, "INSERT INTO posts(user_id, title, content, is_public, created_at) VALUES (?, ?, ?, ?, ?)", posts_rows)

    # Fetch post ids
    cur.execute("SELECT id FROM posts ORDER BY id")
    post_ids = [r[0] for r in cur.fetchall()]

    # ==================== COMMENTS (200+) ====================
    comments_rows = []
    comment_texts = [
        "Great post! Very informative.",
        "Thanks for sharing this knowledge.",
        "I encountered the same issue.",
        "This helped me understand better.",
        "Need more examples though.",
        "Disagree with this approach.",
        "Can you explain further?",
        "Works perfectly for my use case.",
        "Tested and confirmed.",
        "Best practice indeed.",
    ]
    
    for i in range(200):
        post_id = random.choice(post_ids)
        user_id = random.choice(user_list)
        content = comment_texts[i % len(comment_texts)] + f"\nComment #{i+1}"
        comments_rows.append((post_id, user_id, content, now_iso(i % 80)))
    
    insert_many(conn, "INSERT INTO comments(post_id, user_id, content, created_at) VALUES (?, ?, ?, ?)", comments_rows)

    # ==================== SESSIONS (150+) ====================
    sessions_rows = []
    for i in range(150):
        user_id = random.choice(user_list)
        session_token = f"sess_{i:06d}_{random.randint(100000, 999999)}"
        ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        user_agent = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
            "Mozilla/5.0 (X11; Linux x86_64) Firefox/89.0",
            "curl/7.68.0",
            "Python-Requests/2.28.0",
        ])
        sessions_rows.append((user_id, session_token, ip_address, user_agent, now_iso(i % 100), now_iso(0)))
    
    insert_many(conn, "INSERT INTO sessions(user_id, session_token, ip_address, user_agent, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)", sessions_rows)

    # ==================== ATTACK COMMANDS ====================
    attack_commands = [
        ("SQL Injection", "' OR '1'='1", "Test for SQL injection vulnerability", "SELECT * FROM users WHERE id = '1' OR '1'='1'", "Beginner", "Injection"),
        ("XSS Payload", "<script>alert('XSS')</script>", "Cross-site scripting test", "<img src=x onerror='alert(document.cookie)'>", "Beginner", "Injection"),
        ("CSRF Test", "POST /transfer?amount=1000&to=attacker", "Cross-site request forgery", "curl -X POST http://localhost/transfer", "Intermediate", "CSRF"),
        ("Authentication Bypass", "admin' --", "SQL comment injection for bypass", "SELECT * FROM users WHERE username='admin' --'", "Intermediate", "Bypass"),
        ("Brute Force", "for i in range(10000): login(user, password)", "Dictionary attack on login", "hydra -l admin -P passwords.txt http://localhost", "Beginner", "Brute Force"),
        ("Path Traversal", "../../../etc/passwd", "Directory traversal test", "curl http://localhost/file.php?path=../../../../etc/passwd", "Intermediate", "Traversal"),
        ("Command Injection", "; cat /etc/passwd", "OS command injection", "ping -c 1 8.8.8.8; whoami", "Advanced", "Injection"),
        ("File Upload", "shell.php (malicious)", "Upload executable file", "curl -F 'file=@shell.php' http://localhost/upload", "Advanced", "Upload"),
        ("LDAP Injection", "*", "LDAP wildcard injection", "(&(uid=*)(password=*))", "Advanced", "Injection"),
        ("XML Injection", "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>", "XML external entity injection", "POST with XXE payload", "Advanced", "Injection"),
        ("API Enumeration", "curl http://localhost/api/v1/users", "Discover API endpoints", "curl -X GET http://localhost/api/", "Beginner", "Reconnaissance"),
        ("Session Hijacking", "Use stolen session token", "Replay session token", "curl -H 'Cookie: sess_token=...' http://localhost", "Intermediate", "Session"),
    ]
    
    insert_many(conn, "INSERT INTO attack_commands(name, pattern, hint, example, level, category) VALUES (?, ?, ?, ?, ?, ?)", attack_commands)

    # ==================== DEFENSE COMMANDS ====================
    defense_commands = [
        ("Input Validation", "sanitize_input(user_data)", "Validate all user inputs", "if (!preg_match('/^[a-z0-9]+$/i', $input)) reject();", "Beginner", "Prevention"),
        ("Prepared Statements", "SELECT * FROM users WHERE id = ?", "Use parameterized queries", "stmt = conn.prepare('SELECT * FROM users WHERE id = ?')", "Beginner", "Prevention"),
        ("WAF Rules", "mod_security rules", "Deploy web application firewall", "SecRule ARGS:id '@rx ^\\d+$'", "Intermediate", "Detection"),
        ("CSRF Token", "Generate unique token per request", "Implement CSRF tokens", "token = generate_token(); session['csrf'] = token", "Beginner", "Prevention"),
        ("Rate Limiting", "Limit requests per IP/user", "Throttle suspicious activity", "allow_request_if(requests < 100_per_minute)", "Intermediate", "Detection"),
        ("Content Security Policy", "CSP headers", "Restrict script sources", "Content-Security-Policy: default-src 'self'", "Intermediate", "Prevention"),
        ("SQL Query Auditing", "Log all database queries", "Monitor SQL for injection", "audit_log('query', query, user)", "Intermediate", "Detection"),
        ("Session Timeout", "Expire sessions after 30 min", "Limit session duration", "if (time() - session['last_activity'] > 1800) logout()", "Beginner", "Prevention"),
        ("HTTPS Enforcement", "Redirect HTTP to HTTPS", "Use SSL/TLS", "HSTS header + 301 redirect", "Beginner", "Prevention"),
        ("File Upload Filter", "Validate MIME type", "Prevent malicious uploads", "if (mime_type != 'image/jpeg') reject();", "Intermediate", "Prevention"),
        ("Error Handling", "Generic error messages", "Don't expose system details", "return 'An error occurred' instead of stack trace", "Beginner", "Prevention"),
        ("Security Headers", "X-Frame-Options, X-Content-Type", "Set protective headers", "X-Frame-Options: DENY", "Intermediate", "Prevention"),
    ]
    
    insert_many(conn, "INSERT INTO defense_commands(name, pattern, hint, example, level, category) VALUES (?, ?, ?, ?, ?, ?)", defense_commands)

    # ==================== ADMIN LOGS (100+) ====================
    admin_logs_rows = []
    log_actions = [
        "User created",
        "User deleted",
        "Password reset",
        "Post deleted",
        "Comment removed",
        "User banned",
        "Suspicious activity detected",
        "Database backup",
        "Configuration changed",
        "Security update deployed",
    ]
    
    for i in range(100):
        admin_id = user_map["admin"]
        action = random.choice(log_actions)
        details = f"Action #{i+1}: {action} on {now_iso(i % 60)}"
        admin_logs_rows.append((action, admin_id, details, now_iso(i % 70)))
    
    insert_many(conn, "INSERT INTO admin_logs(action, actor_id, details, timestamp) VALUES (?, ?, ?, ?)", admin_logs_rows)

    # ==================== DATABASE RECORDS (80+) ====================
    db_records_rows = []
    for i in range(80):
        record_type = random.choice(["user_data", "transaction", "log_entry", "config", "backup"])
        data = f'{{"type": "{record_type}", "id": {i}, "timestamp": "{now_iso(i % 90)}", "status": "ok"}}'
        is_sensitive = random.choice([0, 1])
        db_records_rows.append((record_type, data, is_sensitive, now_iso(i % 100)))
    
    insert_many(conn, "INSERT INTO database_records(record_type, data, is_sensitive, created_at) VALUES (?, ?, ?, ?)", db_records_rows)

    conn.commit()

    # Export to JSON
    for tbl in ("users", "posts", "comments", "sessions", "attack_commands", "defense_commands", "admin_logs", "database_records"):
        try:
            rows = [dict(r) for r in conn.execute(f"SELECT * FROM {tbl}")]
            with open(os.path.join(BASE_DIR, f"{tbl}.json"), "w", encoding="utf-8") as jf:
                json.dump(rows, jf, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not export {tbl}: {e}")

    conn.close()
    print(f"PwnDora lab database seeded successfully at {DB_PATH}")
    print(f"- Users: {len(users)}")
    print(f"- Posts: {len(posts_rows)}")
    print(f"- Comments: {len(comments_rows)}")
    print(f"- Sessions: {len(sessions_rows)}")
    print(f"- Attack Commands: {len(attack_commands)}")
    print(f"- Defense Commands: {len(defense_commands)}")
    print(f"- Admin Logs: {len(admin_logs_rows)}")
    print(f"- Database Records: {len(db_records_rows)}")
    print(f"- Total Records: {len(users) + len(posts_rows) + len(comments_rows) + len(sessions_rows) + len(attack_commands) + len(defense_commands) + len(admin_logs_rows) + len(db_records_rows)}")


if __name__ == "__main__":
    seed()
