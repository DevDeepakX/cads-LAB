# Open S3 Lab dataset

This folder contains a synthetic dataset and a seeder for the "Open S3 Bucket" lab. All data is dummy and contains no real or sensitive information.

Files created by the seeder:

- `open_s3_lab.db` — SQLite database (created by `seed.py`)
- `buckets.json`, `objects.json`, `access_logs.json`, `fake_credentials.json`, `findings.json` — JSON exports
- `objects/` — directory with small placeholder object files (safe dummy content)

How to run:

```bash
python data/open_s3_lab/seed.py
```

What it models:

- `buckets` — bucket metadata (including `is_public` and `policy`)
- `objects` — object metadata including `acl` and `public_url`
- `access_logs` — simulated S3 access events (LIST/GET/PUT/DELETE)
- `fake_credentials` — intentionally dummy keys for exercises
- `findings` — lab findings / flagged issues

Example quick queries (SQLite):

```sql
-- Find public buckets
SELECT * FROM buckets WHERE is_public=1;

-- List public objects
SELECT * FROM objects WHERE acl LIKE '%public%';

-- Recent anonymous GETs
SELECT * FROM access_logs WHERE requester_identity='Anonymous' AND operation='GET' ORDER BY timestamp DESC LIMIT 50;
```
