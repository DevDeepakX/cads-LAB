#!/usr/bin/env python3
"""Enhanced seed script for Open S3 Bucket lab.

Creates an SQLite DB with:
- Detailed attack and defense commands
- Large dummy dataset (buckets, objects, access logs)
- Realistic security scenarios
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

    # ==================== ATTACK COMMANDS ====================
    attack_commands = [
        ("List S3 Buckets", "aws s3 ls", 
         "Enumerate publicly accessible S3 buckets", 
         "aws s3 ls", "Beginner", "Reconnaissance",
         "List all S3 buckets the attacker can access",
         "open-lab-public\nlab-private\npermissive-policy"),
        
        ("Check Bucket Permissions", "aws s3api list-bucket-acl --bucket {bucket}",
         "Check who has access to a specific bucket",
         "aws s3api list-bucket-acl --bucket open-lab-public",
         "Beginner", "Reconnaissance",
         "Identify bucket access control lists",
         "Owner: arn:aws:iam::123456789:user/admin\nPublic: Yes"),
        
        ("List Bucket Contents", "aws s3 ls s3://{bucket} --recursive",
         "Enumerate objects in a bucket",
         "aws s3 ls s3://open-lab-public --recursive",
         "Beginner", "Exfiltration",
         "Download and review all objects from bucket",
         "2024-01-15 10:23:45 1024 reports/report_001.txt\n2024-01-15 10:24:12 2048 images/img_001.jpg"),
        
        ("Download Object", "aws s3 cp s3://{bucket}/{key} {local_path}",
         "Download a specific object from bucket",
         "aws s3 cp s3://open-lab-public/reports/report_001.txt ./report.txt",
         "Beginner", "Exfiltration",
         "Extract sensitive data from exposed bucket",
         "download: s3://open-lab-public/reports/report_001.txt to ./report.txt"),
        
        ("Bulk Download", "aws s3 sync s3://{bucket} {local_dir}",
         "Recursively download entire bucket",
         "aws s3 sync s3://open-lab-public ./downloaded_data",
         "Intermediate", "Exfiltration",
         "Mass exfiltration of all bucket contents",
         "download: s3://open-lab-public/reports/report_001.txt\ndownload: s3://open-lab-public/images/img_001.jpg"),
        
        ("Check Object ACL", "aws s3api get-object-acl --bucket {bucket} --key {key}",
         "Check individual object permissions",
         "aws s3api get-object-acl --bucket open-lab-public --key reports/report_001.txt",
         "Intermediate", "Reconnaissance",
         "Identify public objects for targeted exfiltration",
         "Owner: arn:aws:iam::123456789:user/admin\nGrantee: Everyone\nPermission: READ"),
        
        ("Access via URL", "curl https://s3.amazonaws.com/{bucket}/{key}",
         "Download object using public URL",
         "curl https://open-lab-public.s3.amazonaws.com/reports/report_001.txt",
         "Beginner", "Exfiltration",
         "Direct HTTP access to public objects",
         "DUMMY REPORT 1\\nTHIS IS FAKE DATA ONLY."),
        
        ("Scan Bucket Policy", "aws s3api get-bucket-policy --bucket {bucket}",
         "Extract bucket policy for analysis",
         "aws s3api get-bucket-policy --bucket permissive-policy",
         "Intermediate", "Reconnaissance",
         "Analyze IAM policies for misconfigurations",
         "Statement: Allow * Principal on s3:*"),
        
        ("List Bucket Versions", "aws s3api list-object-versions --bucket {bucket}",
         "Enumerate object versions for recovery",
         "aws s3api list-object-versions --bucket lab-private",
         "Advanced", "Reconnaissance",
         "Recover deleted objects from bucket versions",
         "Key: secret_doc.txt Version: v1 Status: CURRENT"),
        
        ("Check Bucket Logging", "aws s3api get-bucket-logging --bucket {bucket}",
         "Determine if bucket logs access",
         "aws s3api get-bucket-logging --bucket open-lab-public",
         "Intermediate", "Reconnaissance",
         "Identify if actions are being monitored",
         "LoggingEnabled: false"),
        
        ("Extract Metadata", "aws s3api head-object --bucket {bucket} --key {key}",
         "Get object metadata without downloading",
         "aws s3api head-object --bucket open-lab-public --key reports/report_001.txt",
         "Intermediate", "Reconnaissance",
         "Identify sensitive file properties",
         "ContentType: text/plain Size: 1024 LastModified: 2024-01-15"),
        
        ("Enumerate IAM Roles", "aws iam list-roles",
         "Discover available IAM roles for privilege escalation",
         "aws iam list-roles | grep -i s3",
         "Advanced", "Reconnaissance",
         "Identify potential role assumptions",
         "RoleName: S3AccessRole\nRoleName: LambdaExecutionRole"),
        
        ("Test Write Access", "echo 'evil' | aws s3 cp - s3://{bucket}/malicious.txt",
         "Attempt to upload file to bucket",
         "echo 'test' | aws s3 cp - s3://open-lab-public/test.txt",
         "Advanced", "Persistence",
         "Backdoor bucket with malicious files",
         "upload: - to s3://open-lab-public/test.txt"),
    ]
    
    # ==================== DEFENSE COMMANDS ====================
    defense_commands = [
        ("Enable Versioning", "aws s3api put-bucket-versioning --bucket {bucket} --versioning-configuration Status=Enabled",
         "Enable object versioning for recovery",
         "aws s3api put-bucket-versioning --bucket lab-private --versioning-configuration Status=Enabled",
         "Intermediate", "Protection",
         "Protect against accidental deletion",
         "VersioningConfiguration: Status=Enabled"),
        
        ("Block Public Access", "aws s3api put-public-access-block --bucket {bucket} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
         "Prevent public access to bucket",
         "aws s3api put-public-access-block --bucket open-lab-public --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
         "Beginner", "Protection",
         "Enforce private access controls",
         "PublicAccessBlockConfiguration: All blocks enabled"),
        
        ("Enable Encryption", "aws s3api put-bucket-encryption --bucket {bucket} --server-side-encryption-configuration Rules=[{ApplyServerSideEncryptionByDefault: {SSEAlgorithm: AES256}}]",
         "Enable server-side encryption",
         "aws s3api put-bucket-encryption --bucket lab-private --server-side-encryption-configuration Rules=[{ApplyServerSideEncryptionByDefault: {SSEAlgorithm: AES256}}]",
         "Intermediate", "Protection",
         "Encrypt all objects at rest",
         "ServerSideEncryptionConfiguration: Enabled"),
        
        ("Enable Logging", "aws s3api put-bucket-logging --bucket {bucket} --bucket-logging-status LoggingEnabled={TargetBucket: logs-bucket,TargetPrefix: access-logs/}",
         "Enable S3 access logging",
         "aws s3api put-bucket-logging --bucket open-lab-public --bucket-logging-status LoggingEnabled={TargetBucket: logs-bucket,TargetPrefix: access-logs/}",
         "Intermediate", "Detection",
         "Monitor all bucket access",
         "LoggingEnabled: true TargetBucket: logs-bucket"),
        
        ("Set Restrictive Policy", "aws s3api put-bucket-policy --bucket {bucket} --policy file://policy.json",
         "Apply restrictive bucket policy",
         "aws s3api put-bucket-policy --bucket lab-private --policy file://restrictive-policy.json",
         "Advanced", "Protection",
         "Limit access to specific principals/IPs",
         "BucketPolicy: Applied successfully"),
        
        ("Remove Public ACLs", "aws s3api put-object-acl --bucket {bucket} --key {key} --acl private",
         "Change object from public to private",
         "aws s3api put-object-acl --bucket open-lab-public --key reports/report_001.txt --acl private",
         "Intermediate", "Remediation",
         "Revoke public access to specific objects",
         "ObjectACL: private"),
        
        ("Enable MFA Delete", "aws s3api put-bucket-versioning --bucket {bucket} --versioning-configuration Status=Enabled,MFADelete=Enabled",
         "Require MFA for object deletion",
         "aws s3api put-bucket-versioning --bucket lab-private --versioning-configuration Status=Enabled,MFADelete=Enabled",
         "Advanced", "Protection",
         "Add extra layer of deletion protection",
         "MFADeleteConfiguration: Enabled"),
        
        ("Set Lifecycle Policy", "aws s3api put-bucket-lifecycle-configuration --bucket {bucket} --lifecycle-configuration file://lifecycle.json",
         "Implement automatic object expiration",
         "aws s3api put-bucket-lifecycle-configuration --bucket lab-private --lifecycle-configuration file://lifecycle.json",
         "Advanced", "Protection",
         "Automatically delete old or sensitive objects",
         "LifecycleConfiguration: Applied"),
        
        ("Audit Access Logs", "aws s3 cp s3://logs-bucket/access-logs/ ./logs --recursive && grep -E 'GET|PUT' ./logs/*.log",
         "Analyze bucket access logs for intrusions",
         "aws s3 cp s3://logs-bucket/access-logs/ ./logs --recursive && grep 'Anonymous' ./logs/*.log | wc -l",
         "Advanced", "Detection",
         "Identify suspicious access patterns",
         "Found 42 anonymous access attempts in last 7 days"),
        
        ("Enable CloudTrail", "aws cloudtrail put-event-selectors --trail-name my-trail --event-selectors ReadWriteType=All,IncludeManagementEvents=true,DataResources=[{Type: AWS::S3::Object,Values: [arn:aws:s3:::bucket/*]}]",
         "Log all S3 API calls",
         "aws cloudtrail create-trail --name s3-audit-trail --s3-bucket-name audit-bucket",
         "Advanced", "Detection",
         "Track all API calls for compliance",
         "TrailStatus: Enabled"),
        
        ("Set Bucket Tags", "aws s3api put-bucket-tagging --bucket {bucket} --tagging TagSet=[{Key: Environment,Value: Production},{Key: DataClassification,Value: Sensitive}]",
         "Tag bucket for governance",
         "aws s3api put-bucket-tagging --bucket lab-private --tagging TagSet=[{Key: DataType,Value: Confidential}]",
         "Beginner", "Management",
         "Organize and track sensitive buckets",
         "BucketTags: Applied"),
        
        ("Enable Requester Pays", "aws s3api put-bucket-request-payment --bucket {bucket} --request-payment-configuration Payer=Requester",
         "Prevent cost exploitation",
         "aws s3api put-bucket-request-payment --bucket open-lab-public --request-payment-configuration Payer=Requester",
         "Intermediate", "Protection",
         "Control who pays for data transfer",
         "RequesterPaysConfiguration: Enabled"),
        
        ("Scan for Sensitive Data", "aws s3 ls s3://{bucket} --recursive | grep -iE 'password|secret|key|api|credential|token'",
         "Find potentially sensitive files",
         "aws s3 ls s3://open-lab-public --recursive | grep -iE 'password|secret|key'",
         "Intermediate", "Detection",
         "Proactively identify risky files",
         "Found: secret_keys.txt, aws_credentials.json, password_list.csv"),
    ]
    
    # ==================== LEVELS ====================
    levels = [
        ("Beginner", "Basic S3 operations and reconnaissance"),
        ("Intermediate", "Advanced enumeration and defense tactics"),
        ("Advanced", "Complex privilege escalation and compliance"),
    ]
    
    insert_many(conn, "INSERT INTO levels(name, description) VALUES (?, ?)", levels)
    insert_many(conn, "INSERT INTO attack_commands(name, pattern, hint, example, level, category, description, expected_output) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", attack_commands)
    insert_many(conn, "INSERT INTO defense_commands(name, pattern, hint, example, level, category, description, expected_output) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", defense_commands)

    # ==================== BUCKETS ====================
    buckets = [
        ("open-lab-public", "us-east-1", "lab-team", 1, None, now_iso(60)),
        ("lab-private", "us-west-2", "lab-team", 0, None, now_iso(90)),
        ("permissive-policy", "eu-west-1", "lab-team", 1, '{"Statement": "Allow *"}', now_iso(30)),
        ("backup-vault", "ap-southeast-1", "backup-admin", 0, None, now_iso(180)),
        ("logs-bucket", "eu-central-1", "monitoring", 0, None, now_iso(45)),
    ]
    insert_many(conn, "INSERT INTO buckets(name, region, owner, is_public, policy, created_at) VALUES (?, ?, ?, ?, ?, ?)", buckets)

    # Fetch bucket ids
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM buckets")
    bucket_map = {r[1]: r[0] for r in cur.fetchall()}

    # ==================== OBJECTS ====================
    objects_rows = []
    object_files = []

    # Public bucket: 200+ objects
    pub_id = bucket_map["open-lab-public"]
    for i in range(1, 201):
        if i % 15 == 0:
            key = f"images/img_{i:04d}.jpg"
            ctype = "image/jpeg"
            content = f"DUMMY IMAGE {i}\nNO SENSITIVE DATA\n"
        elif i % 8 == 0:
            key = f"documents/doc_{i:04d}.pdf"
            ctype = "application/pdf"
            content = f"DUMMY PDF {i}\nNO SENSITIVE DATA\n"
        else:
            key = f"reports/report_{i:04d}.txt"
            ctype = "text/plain"
            content = f"DUMMY REPORT {i}\nGenerated: 2024-01-{(i%28)+1:02d}\nStatus: OK\n"
        size = len(content.encode("utf-8"))
        last_modified = now_iso(i % 45)
        acl = "public-read" if i % 5 != 0 else "private"
        public_url = f"https://open-lab-public.s3.amazonaws.com/{key}" if acl == "public-read" else None
        objects_rows.append((pub_id, key, size, ctype, last_modified, "STANDARD", acl, public_url))
        if len(object_files) < 150:
            object_files.append(("open-lab-public", key, content))

    # Private bucket: 100+ objects
    priv_id = bucket_map["lab-private"]
    for i in range(1, 101):
        if i % 10 == 0:
            key = f"sensitive/config_{i:03d}.json"
            ctype = "application/json"
            content = f'{{"db_host": "db.internal", "port": 5432, "version": {i}}}\n'
        else:
            key = f"data/private_doc_{i:03d}.txt"
            ctype = "text/plain"
            content = f"PRIVATE DATA {i}\nClassification: Confidential\nNo public access\n"
        size = len(content.encode("utf-8"))
        last_modified = now_iso(i % 60)
        acl = "private"
        objects_rows.append((priv_id, key, size, ctype, last_modified, "STANDARD", acl, None))
        if len(object_files) < 150:
            object_files.append(("lab-private", key, content))

    # Permissive policy bucket: 150+ objects
    perm_id = bucket_map["permissive-policy"]
    for i in range(1, 151):
        if i % 20 == 0:
            key = f"logs/audit_{i:04d}.log"
            ctype = "text/plain"
            content = f"[2024-01-15 10:{(i%60):02d}:00] AUDIT: User admin performed action s3:ListBucket\n"
        else:
            key = f"uploads/file_{i:04d}.dat"
            ctype = "application/octet-stream"
            content = f"DATA_BLOCK_{i}\n" * 10
        size = len(content.encode("utf-8"))
        last_modified = now_iso(i % 30)
        acl = "public-read" if i % 7 == 0 else "private"
        public_url = f"https://permissive-policy.s3.amazonaws.com/{key}" if acl == "public-read" else None
        objects_rows.append((perm_id, key, size, ctype, last_modified, "STANDARD", acl, public_url))
        if len(object_files) < 150:
            object_files.append(("permissive-policy", key, content))

    # Backup vault: 80+ objects
    backup_id = bucket_map["backup-vault"]
    for i in range(1, 81):
        key = f"backups/backup_{i:04d}.tar.gz"
        ctype = "application/gzip"
        content = f"BACKUP_DATA_{i}\nCompressed database backup\n" * 5
        size = len(content.encode("utf-8"))
        last_modified = now_iso(i % 90)
        acl = "private"
        objects_rows.append((backup_id, key, size, ctype, last_modified, "GLACIER", acl, None))
        if len(object_files) < 150:
            object_files.append(("backup-vault", key, content))

    insert_many(conn, "INSERT INTO objects(bucket_id, key, size_bytes, content_type, last_modified, storage_class, acl, public_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", objects_rows)

    # ==================== ACCESS LOGS ====================
    cur.execute("SELECT id, bucket_id, key FROM objects")
    objs = cur.fetchall()
    objs_by_bucket = {}
    for r in objs:
        objs_by_bucket.setdefault(r[1], []).append((r[0], r[2]))

    logs = []
    sample_ips = [f"203.0.113.{i}" for i in range(5, 100)] + [f"198.51.100.{i}" for i in range(10, 120)]
    user_agents = ["curl/7.68.0", "aws-cli/2.4.7", "Mozilla/5.0", "wget/1.20.3", "python-requests/2.28"]

    # LIST events on public bucket (many)
    for i in range(50):
        logs.append((pub_id, None, now_iso(i % 10), random.choice(sample_ips), random.choice(user_agents), "Anonymous", "LIST", 200, 0, None))

    # GET events for public objects (many)
    pub_objs = objs_by_bucket.get(pub_id, [])[:100]
    for i, (obj_id, key) in enumerate(pub_objs):
        logs.append((pub_id, obj_id, now_iso(i % 15), random.choice(sample_ips), random.choice(user_agents), "Anonymous", "GET", 200, random.randint(64, 4096), None))

    # Failed access attempts on private bucket
    for i in range(15):
        logs.append((priv_id, None, now_iso(i % 20), f"203.0.113.{100+i}", "malicious-scanner/1.0", "Anonymous", "LIST", 403, 0, None))

    # Successful internal accesses
    for i in range(30):
        logs.append((backup_id, None, now_iso(i % 25), "10.0.0.5", "aws-cli/2.4.7", "arn:aws:iam::123456789:user/backup-admin", "GET", 200, random.randint(1024, 10240), None))

    insert_many(conn, "INSERT INTO access_logs(bucket_id, object_id, timestamp, requester_ip, requester_agent, requester_identity, operation, status_code, bytes_sent, referrer) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", logs)

    # ==================== FAKE CREDENTIALS ====================
    creds = [
        ("AKIAIOSFODNN7EXAMPLE1", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "test-attacker-1", 1, now_iso(100)),
        ("AKIAIOSFODNN7EXAMPLE2", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2", "test-attacker-2", 0, now_iso(50)),
        ("AKIAJ7XAMPLE0001S3OP", "SuperSecretKeyWith32Characters1234567890", "s3-user", 1, now_iso(200)),
    ]
    insert_many(conn, "INSERT INTO fake_credentials(access_key, secret_key, created_for, is_active, created_at) VALUES (?, ?, ?, ?, ?)", creds)

    # ==================== FINDINGS ====================
    findings = [
        (pub_id, None, "Bucket Publicly Listed", "open-lab-public bucket allows anonymous LIST operation", "CRITICAL", now_iso(1), 0),
        (pub_id, None, "Public Read Access", "Multiple objects in bucket have public-read ACL", "HIGH", now_iso(2), 0),
        (perm_id, None, "Permissive IAM Policy", "Bucket policy allows * principal on s3:*", "CRITICAL", now_iso(3), 0),
        (None, None, "Exposed Credentials", "AWS access keys found in public objects", "CRITICAL", now_iso(4), 0),
        (backup_id, None, "No Encryption", "Backup vault does not have server-side encryption enabled", "HIGH", now_iso(5), 0),
    ]
    insert_many(conn, "INSERT INTO findings(bucket_id, object_id, title, description, severity, reported_at, resolved) VALUES (?, ?, ?, ?, ?, ?, ?)", findings)

    conn.commit()

    # Create small object files
    for bucket_name, key, content in object_files[:150]:
        bucket_path = os.path.join(OBJECTS_DIR, bucket_name)
        os.makedirs(bucket_path, exist_ok=True)
        full_path = os.path.join(bucket_path, *key.split("/"))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    # JSON exports
    for tbl in ("buckets", "objects", "access_logs", "fake_credentials", "findings", "attack_commands", "defense_commands"):
        try:
            rows = [dict(r) for r in conn.execute(f"SELECT * FROM {tbl}")]
            with open(os.path.join(BASE_DIR, f"{tbl}.json"), "w", encoding="utf-8") as jf:
                json.dump(rows, jf, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not export {tbl}: {e}")

    conn.close()
    print(f"Enhanced seed complete. DB: {DB_PATH}")
    print(f"- Buckets: {len(buckets)}")
    print(f"- Objects: {len(objects_rows)}")
    print(f"- Access Logs: {len(logs)}")
    print(f"- Attack Commands: {len(attack_commands)}")
    print(f"- Defense Commands: {len(defense_commands)}")
    print(f"- Total Data Points: {len(buckets) + len(objects_rows) + len(logs) + len(attack_commands) + len(defense_commands)}")


if __name__ == "__main__":
    seed()
