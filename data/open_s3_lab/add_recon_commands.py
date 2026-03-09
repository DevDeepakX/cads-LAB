#!/usr/bin/env python3
"""
Add comprehensive S3 reconnaissance commands to the Open S3 Bucket lab database.
These commands help attackers gather information about S3 buckets and their contents.
"""

import sqlite3

# Connect to the database
DB_PATH = "open_s3_lab.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Define reconnaissance commands with detailed hints
recon_commands = [
    {
        "name": "Enumerate Public Buckets",
        "pattern": "aws s3api list-buckets",
        "hint": "List all accessible S3 buckets. This is often the first step in reconnaissance.",
        "example": "aws s3api list-buckets --profile attacker",
        "level": "Beginner",
        "category": "Reconnaissance",
        "description": "Lists all S3 buckets visible to the current AWS credentials",
        "expected_output": "Buckets with names, creation dates, and owner information"
    },
    {
        "name": "Check Bucket Public Access Block",
        "pattern": "aws s3api get-public-access-block --bucket {bucket}",
        "hint": "Determine if a bucket has public access restrictions enabled",
        "example": "aws s3api get-public-access-block --bucket target-bucket --region us-east-1",
        "level": "Beginner",
        "category": "Reconnaissance",
        "description": "Retrieves the public access block settings for a bucket",
        "expected_output": "PublicAccessBlockConfiguration with block flags"
    },
    {
        "name": "Scan Bucket for Website Configuration",
        "pattern": "aws s3api get-bucket-website --bucket {bucket}",
        "hint": "Check if bucket is configured to host a static website",
        "example": "aws s3api get-bucket-website --bucket target-bucket --region us-east-1",
        "level": "Beginner",
        "category": "Reconnaissance",
        "description": "Checks if bucket is configured as a website endpoint",
        "expected_output": "Website configuration including index and error documents"
    },
    {
        "name": "Retrieve Bucket Region",
        "pattern": "aws s3api get-bucket-location --bucket {bucket}",
        "hint": "Identify the AWS region where a bucket is located",
        "example": "aws s3api get-bucket-location --bucket target-bucket",
        "level": "Beginner",
        "category": "Reconnaissance",
        "description": "Determines the region where bucket is stored",
        "expected_output": "LocationConstraint value (e.g., us-west-2)"
    },
    {
        "name": "List Object Tags",
        "pattern": "aws s3api get-object-tagging --bucket {bucket} --key {key}",
        "hint": "Extract metadata tags from objects which may reveal sensitive info",
        "example": "aws s3api get-object-tagging --bucket target-bucket --key sensitive.txt",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Retrieves tags associated with an object",
        "expected_output": "TagSet with key-value pairs"
    },
    {
        "name": "Check Bucket Versioning Status",
        "pattern": "aws s3api get-bucket-versioning --bucket {bucket}",
        "hint": "Determine if versioning is enabled (may allow recovering deleted objects)",
        "example": "aws s3api get-bucket-versioning --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Shows versioning configuration of the bucket",
        "expected_output": "MFADelete and Status settings"
    },
    {
        "name": "Enumerate Server-Side Encryption",
        "pattern": "aws s3api get-bucket-encryption --bucket {bucket}",
        "hint": "Identify if bucket uses encryption and what type (KMS vs SSE-S3)",
        "example": "aws s3api get-bucket-encryption --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Checks what encryption method is applied to bucket",
        "expected_output": "ServerSideEncryptionConfiguration details"
    },
    {
        "name": "Check Request Payment Configuration",
        "pattern": "aws s3api get-bucket-request-payment --bucket {bucket}",
        "hint": "Determine who pays for data transfer costs (requester vs owner)",
        "example": "aws s3api get-bucket-request-payment --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Checks if requester must pay for bandwidth",
        "expected_output": "Payer: Requester or BucketOwner"
    },
    {
        "name": "Enumerate Access Control Lists",
        "pattern": "aws s3api get-bucket-acl --bucket {bucket}",
        "hint": "List all users/groups with access to the bucket and their permissions",
        "example": "aws s3api get-bucket-acl --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Retrieves bucket-level access control list",
        "expected_output": "Owner and Grants with Read/Write/ReadAcp/WriteAcp permissions"
    },
    {
        "name": "Scan for CORS Configuration",
        "pattern": "aws s3api get-bucket-cors --bucket {bucket}",
        "hint": "Check if bucket allows cross-origin requests (potential for XSS attacks)",
        "example": "aws s3api get-bucket-cors --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Retrieves CORS configuration allowing cross-origin access",
        "expected_output": "CORSRules with allowed methods and origins"
    },
    {
        "name": "Check Bucket Lifecycle Rules",
        "pattern": "aws s3api get-bucket-lifecycle-configuration --bucket {bucket}",
        "hint": "Identify policies for object retention/deletion (may reveal data patterns)",
        "example": "aws s3api get-bucket-lifecycle-configuration --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Retrieves lifecycle policies for automated object management",
        "expected_output": "Rules with transitions and expirations"
    },
    {
        "name": "Enumerate CloudFront Distributions",
        "pattern": "aws cloudfront list-distributions",
        "hint": "Find CDN distributions pointing to S3 buckets",
        "example": "aws cloudfront list-distributions --profile attacker",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Lists all CloudFront distributions (may use S3 as origin)",
        "expected_output": "Distribution IDs and domain names"
    },
    {
        "name": "Check for Logging Configuration",
        "pattern": "aws s3api get-bucket-logging --bucket {bucket}",
        "hint": "Determine if bucket logs access (will reveal if actions are being monitored)",
        "example": "aws s3api get-bucket-logging --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Shows if access logging is enabled and where logs are stored",
        "expected_output": "LoggingEnabled with target bucket and prefix"
    },
    {
        "name": "Scan for Notification Configuration",
        "pattern": "aws s3api get-bucket-notification-configuration --bucket {bucket}",
        "hint": "Identify SNS/SQS topics or Lambda functions triggered by bucket events",
        "example": "aws s3api get-bucket-notification-configuration --bucket target-bucket --region us-east-1",
        "level": "Advanced",
        "category": "Reconnaissance",
        "description": "Reveals event notifications configuration",
        "expected_output": "TopicConfiguration, QueueConfiguration, or LambdaFunctionConfiguration"
    },
    {
        "name": "Check Replication Rules",
        "pattern": "aws s3api get-bucket-replication --bucket {bucket}",
        "hint": "Identify if bucket is replicating data to other buckets",
        "example": "aws s3api get-bucket-replication --bucket target-bucket --region us-east-1",
        "level": "Advanced",
        "category": "Reconnaissance",
        "description": "Shows cross-region or same-region replication rules",
        "expected_output": "ReplicationConfiguration with destination buckets"
    },
    {
        "name": "Enumerate Object Lock Configuration",
        "pattern": "aws s3api get-object-lock-configuration --bucket {bucket}",
        "hint": "Check if bucket has WORM (Write Once Read Many) protection enabled",
        "example": "aws s3api get-object-lock-configuration --bucket target-bucket --region us-east-1",
        "level": "Advanced",
        "category": "Reconnaissance",
        "description": "Determines if object lock prevents deletion/modification",
        "expected_output": "ObjectLockConfiguration with retention settings"
    },
    {
        "name": "Check Intelligent-Tiering Configuration",
        "pattern": "aws s3api get-bucket-intelligent-tiering-configuration --bucket {bucket} --id {id}",
        "hint": "Identify automatic storage tier transition policies",
        "example": "aws s3api list-bucket-intelligent-tiering-configurations --bucket target-bucket",
        "level": "Advanced",
        "category": "Reconnaissance",
        "description": "Shows automatic storage class transitions",
        "expected_output": "IntelligentTieringConfiguration with tier transitions"
    },
    {
        "name": "Scan for Bucket Policies",
        "pattern": "aws s3api get-bucket-policy --bucket {bucket}",
        "hint": "Extract bucket policy to identify allowed/denied actions and principals",
        "example": "aws s3api get-bucket-policy --bucket target-bucket --region us-east-1",
        "level": "Intermediate",
        "category": "Reconnaissance",
        "description": "Retrieves the bucket policy which controls access",
        "expected_output": "Policy JSON with Effect, Principal, Action, and Resource"
    },
]

# Insert commands
inserted = 0
skipped = 0

for cmd in recon_commands:
    try:
        cur.execute("""
            INSERT INTO attack_commands 
            (name, pattern, hint, example, level, category, description, expected_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cmd["name"],
            cmd["pattern"],
            cmd["hint"],
            cmd["example"],
            cmd["level"],
            cmd["category"],
            cmd["description"],
            cmd["expected_output"]
        ))
        inserted += 1
        print(f"✓ Added: {cmd['name']}")
    except sqlite3.IntegrityError:
        skipped += 1
        print(f"⊘ Skipped (exists): {cmd['name']}")
    except Exception as e:
        print(f"✗ Error adding {cmd['name']}: {e}")

conn.commit()
conn.close()

print(f"\nResults:")
print(f"  Inserted: {inserted}")
print(f"  Skipped: {skipped}")
print(f"  Total: {inserted + skipped}")
print(f"\nS3 Reconnaissance commands saved to {DB_PATH}")
