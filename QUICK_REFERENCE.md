# Quick Reference: S3 Reconnaissance Commands

## Command Categories & Difficulty Levels

### BEGINNER (6 commands) - Basic Enumeration
```
1. Enumerate Public Buckets           aws s3api list-buckets
2. Check Bucket Permissions           aws s3api list-bucket-acl --bucket {bucket}
3. Check Bucket Public Access Block   aws s3api get-public-access-block --bucket {bucket}
4. Scan Bucket for Website Config     aws s3api get-bucket-website --bucket {bucket}
5. Retrieve Bucket Region             aws s3api get-bucket-location --bucket {bucket}
6. List S3 Buckets                    aws s3 ls
```

### INTERMEDIATE (14 commands) - Configuration Discovery
```
1. Check Object ACL                   aws s3api get-object-acl --bucket {bucket} --key {key}
2. Scan Bucket Policy                 aws s3api get-bucket-policy --bucket {bucket}
3. Check Bucket Logging               aws s3api get-bucket-logging --bucket {bucket}
4. Extract Metadata                   aws s3api head-object --bucket {bucket} --key {key}
5. List Object Tags                   aws s3api get-object-tagging --bucket {bucket} --key {key}
6. Check Bucket Versioning Status     aws s3api get-bucket-versioning --bucket {bucket}
7. Enumerate Server-Side Encryption   aws s3api get-bucket-encryption --bucket {bucket}
8. Check Request Payment Config       aws s3api get-bucket-request-payment --bucket {bucket}
9. Enumerate Access Control Lists     aws s3api get-bucket-acl --bucket {bucket}
10. Scan for CORS Configuration       aws s3api get-bucket-cors --bucket {bucket}
11. Check Bucket Lifecycle Rules      aws s3api get-bucket-lifecycle-configuration --bucket {bucket}
12. Enumerate CloudFront Distros      aws cloudfront list-distributions
13. Check Logging Configuration       aws s3api get-bucket-logging --bucket {bucket}
14. Scan for Bucket Policies          aws s3api get-bucket-policy --bucket {bucket}
```

### ADVANCED (6 commands) - Complex Scenarios
```
1. List Bucket Versions               aws s3api list-object-versions --bucket {bucket}
2. Enumerate IAM Roles                aws iam list-roles
3. Scan Notification Configuration    aws s3api get-bucket-notification-configuration --bucket {bucket}
4. Check Replication Rules            aws s3api get-bucket-replication --bucket {bucket}
5. Enumerate Object Lock Config       aws s3api get-object-lock-configuration --bucket {bucket}
6. Check Intelligent-Tiering Config   aws s3api list-bucket-intelligent-tiering-configurations --bucket {bucket}
```

## Rate Limiting Rules (Per Lab)

| View # | Status | Can View |
|--------|--------|----------|
| 1st    | Free   | ✅ Yes   |
| 2nd    | Free   | ✅ Yes   |
| 3rd    | Free   | ✅ Yes   |
| 4th    | Limited| ❌ No (wait 5 min) |
| 5th+   | Limited| ❌ No (wait 5 min) |

**After 5 minutes**: View counter resets, can view 3 more times

**Switching Labs**: Each lab has independent counter
- S3 Lab: 3 views
- PwnDora Lab: 3 views (independent)
- Network Lab: 3 views (independent)

## Features

### Security
- ✅ Screenshot prevention (enabled when open)
- ✅ Rate limiting (3 free/lab, 5-min cooldown)
- ✅ Lab-specific tracking
- ✅ Session-based enforcement

### User Experience
- ✅ Thief emoji (🕵️‍♂️) button for easy access
- ✅ Dark theme modal interface
- ✅ Commands organized by difficulty
- ✅ Hints explain each command's purpose
- ✅ Working examples for every command

### Data Quality
- ✅ 26 commands total
- ✅ 100% hints populated
- ✅ 100% examples provided
- ✅ 100% descriptions included

## Example: Using the Cheatsheet

```
Step 1: Start Lab
  → Choose "Open S3 Bucket" lab
  → Select "Attack" mode

Step 2: Open Cheatsheet
  → Click 🕵️‍♂️ button
  → Modal opens with commands

Step 3: Select Command
  → Browse "Beginner" commands
  → Pick "Enumerate Public Buckets"
  → See hint: "List all accessible S3 buckets"

Step 4: Copy & Execute
  → Copy example: "aws s3api list-buckets"
  → Paste in terminal
  → Execute to enumerate buckets

Step 5: Track Usage
  → First open: "Free view 1/3"
  → Second open: "Free view 2/3"
  → Third open: "Free view 3/3"
  → Fourth open: "Rate limited - wait 5 minutes"
```

## Database Location

```
data/open_s3_lab/open_s3_lab.db

Tables:
  - attack_commands (31 total)
    ├── Reconnaissance: 26 ✅
    ├── Exfiltration: 4
    └── Persistence: 1
  - defense_commands (13 total)
  - buckets, objects, access_logs, etc.
```

## API Endpoint

```
GET /cheatsheet_api

Request: (Session-based authentication)
  - Mode: session["mode"] (attack/defense)
  - Lab: Automatically determined from session

Response:
{
  "commands": [
    {
      "name": "Enumerate Public Buckets",
      "pattern": "aws s3api list-buckets",
      "description": "List all accessible S3 buckets...",
      "example": "aws s3api list-buckets --profile attacker",
      "level": "Beginner"
    },
    ...
  ],
  "mode": "attack",
  "remaining_free_views": 2,
  "lab": "s3"
}

Error Response (429 Too Many Requests):
{
  "error": "Rate limit exceeded",
  "message": "Cheatsheet for s3 lab available again in 287 seconds",
  "commands": [],
  "mode": "attack"
}
```

## Quick Stats

- **Total Commands**: 26 reconnaissance
- **Beginner Commands**: 6
- **Intermediate Commands**: 14
- **Advanced Commands**: 6
- **Data Completeness**: 100%
- **Free Views/Lab**: 3
- **Cooldown Period**: 5 minutes
- **Labs Covered**: 3 (S3, PwnDora, Network)

---

**Status**: ✅ PRODUCTION READY

All reconnaissance commands are properly stored, validated, and integrated with the secure cheatsheet system.
