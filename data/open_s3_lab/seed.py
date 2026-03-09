#!/usr/bin/env python3
"""Seed script for Open S3 Bucket lab.

Creates an SQLite DB at `open_s3_lab.db`, populates tables with deterministic
dummy data, writes JSON exports, and creates small placeholder object files.
"""
from __future__ import annotations
import sqlite3
import json
import os
import random
from datetime import datetime, timezone, timedelta


BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "open_s3_lab.db")
OBJECTS_DIR = os.path.join(BASE_DIR, "objects")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")


def now_iso(delta_days=0):
    return (datetime.now(timezone.utc) - timedelta(days=delta_days)).isoformat()


def ensure_dirs():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(OBJECTS_DIR, exist_ok=True)


def load_schema(conn: sqlite3.Connection):
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def insert_many(conn, sql, rows):
    cur = conn.cursor()
    cur.executemany(sql, rows)
    return cur


def seed():
    random.seed(42)
    ensure_dirs()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    load_schema(conn)

    # Buckets
    buckets = [
        ("open-lab-public", "us-east-1", "lab-team", 1, None, now_iso(60)),
        ("lab-private", "us-west-2", "lab-team", 0, None, now_iso(90)),
        ("permissive-policy", "eu-west-1", "lab-team", 1, '{"Statement": "Allow *"}', now_iso(30)),
    ]
    insert_many(conn, "INSERT INTO buckets(name,region,owner,is_public,policy,created_at) VALUES (?,?,?,?,?,?)", buckets)

    # Fetch bucket ids
    cur = conn.cursor()
    cur.execute("SELECT id,name FROM buckets")
    bucket_map = {r[1]: r[0] for r in cur.fetchall()}

    # Objects
    objects_rows = []
    object_files = []

    # Public bucket: many small objects
    pub_id = bucket_map["open-lab-public"]
    for i in range(1, 101):
        if i % 10 == 0:
            key = f"images/img_{i:03d}.jpg"
            ctype = "image/jpeg"
            content = f"DUMMY IMAGE {i}\nNO SENSITIVE DATA\n"
        else:
            key = f"reports/report_{i:03d}.txt"
            ctype = "text/plain"
            content = f"DUMMY REPORT {i}\nTHIS IS FAKE DATA ONLY.\n"
        size = len(content.encode("utf-8"))
        last_modified = now_iso(i % 7)
        acl = "public-read"
        public_url = f"https://example.local/{key}"
        objects_rows.append((pub_id, key, size, ctype, last_modified, "STANDARD", acl, public_url))
        object_files.append(("open-lab-public", key, content))

    # Private bucket: fewer objects
    priv_id = bucket_map["lab-private"]
    for i in range(1, 21):
        key = f"docs/doc_{i:02d}.txt"
        content = f"DUMMY PRIVATE DOC {i}\nNO SENSITIVE DATA\n"
        size = len(content.encode("utf-8"))
        last_modified = now_iso(i % 14)
        acl = "private"
        objects_rows.append((priv_id, key, size, "text/plain", last_modified, "STANDARD", acl, None))
        object_files.append(("lab-private", key, content))

    # Permissive policy bucket: mix
    perm_id = bucket_map["permissive-policy"]
    for i in range(1, 31):
        key = f"logs/log_{i:03d}.log"
        content = f"DUMMY LOG {i}\nentry=ok\n"
        size = len(content.encode("utf-8"))
        last_modified = now_iso(i % 5)
        acl = "public-read" if i % 5 == 0 else "private"
        public_url = f"https://example.local/{key}" if acl != "private" else None
        objects_rows.append((perm_id, key, size, "text/plain", last_modified, "STANDARD", acl, public_url))
        object_files.append(("permissive-policy", key, content))

    insert_many(conn, "INSERT INTO objects(bucket_id,key,size_bytes,content_type,last_modified,storage_class,acl,public_url) VALUES (?,?,?,?,?,?,?,?)", objects_rows)

    # Fetch object ids for logs
    cur.execute("SELECT id,bucket_id,key FROM objects")
    objs = cur.fetchall()
    objs_by_bucket = {}
    for r in objs:
        objs_by_bucket.setdefault(r[1], []).append((r[0], r[2]))

    # Access logs: simulate anonymous listing and GETs
    logs = []
    sample_ips = [f"203.0.113.{i}" for i in range(5, 50)] + [f"198.51.100.{i}" for i in range(10, 60)]
    user_agents = ["curl/7.68.0", "aws-cli/2.0", "Mozilla/5.0 (compatible)"]

    # LIST events on public bucket
    for i in range(10):
        logs.append((pub_id, None, now_iso(i), random.choice(sample_ips), random.choice(user_agents), "Anonymous", "LIST", 200, 0, None))

    # GET events for a subset of public objects
    pub_objs = objs_by_bucket.get(pub_id, [])[:30]
    for i, (obj_id, key) in enumerate(pub_objs):
        logs.append((pub_id, obj_id, now_iso(i), random.choice(sample_ips), random.choice(user_agents), "Anonymous", "GET", 200, random.randint(64, 2048), None))

    # Some failed attempts
    logs.append((priv_id, None, now_iso(1), "203.0.113.99", "malicious-scanner/1.0", "Anonymous", "LIST", 403, 0, None))
    logs.append((perm_id, None, now_iso(2), "198.51.100.77", "fuzzer/0.1", "Anonymous", "GET", 404, 0, None))

    insert_many(conn, "INSERT INTO access_logs(bucket_id,object_id,timestamp,requester_ip,requester_agent,requester_identity,operation,status_code,bytes_sent,referrer) VALUES (?,?,?,?,?,?,?,?,?,?)", logs)

    # Fake credentials
    creds = [
        ("AKIAEXAMPLE0001", "shhh-secret-0001", "test-actor", 0, now_iso(100)),
        ("AKIAEXAMPLE0002", "shhh-secret-0002", "test-actor", 1, now_iso(10)),
    ]
    insert_many(conn, "INSERT INTO fake_credentials(access_key,secret_key,created_for,is_active,created_at) VALUES (?,?,?,?,?)", creds)

    # Findings
    findings = [
        (pub_id, None, "Public bucket exposed", "Bucket `open-lab-public` is publicly listable.", "HIGH", now_iso(1), 0),
    ]
    insert_many(conn, "INSERT INTO findings(bucket_id,object_id,title,description,severity,reported_at,resolved) VALUES (?,?,?,?,?,?,?)", findings)

    conn.commit()

    # Create small object files for first N objects (safe placeholders)
    for bucket_name, key, content in object_files[:80]:
        bucket_path = os.path.join(OBJECTS_DIR, bucket_name)
        os.makedirs(bucket_path, exist_ok=True)
        # create nested directories if key has path
        full_path = os.path.join(bucket_path, *key.split("/"))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    # JSON exports
    for tbl in ("buckets", "objects", "access_logs", "fake_credentials", "findings"):
        rows = [dict(r) for r in conn.execute(f"SELECT * FROM {tbl}")]
        with open(os.path.join(BASE_DIR, f"{tbl}.json"), "w", encoding="utf-8") as jf:
            json.dump(rows, jf, indent=2, default=str)

    conn.close()
    print(f"Seed complete. DB: {DB_PATH}")


if __name__ == "__main__":
    seed()
