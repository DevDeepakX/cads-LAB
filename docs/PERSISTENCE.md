# Persistence

Phase 5 uses the existing SQLite database foundation. The Flask factory passes its configured `DATABASE_URL` to `SimulatorProvider`, so resources and events are loaded from the database after process restart. `FindingEngine` uses the same database when attached to a persistent provider.

## Relationships

```text
User
  -> lab_sessions
      -> cloud_resources
      -> cloud_events
      -> findings
      -> objective_progress
      -> score_events
```

The JSON lab definition remains the source for lab content. Starting a persistent session reconciles that definition into the existing `labs` catalog row, then creates or resumes one owned session for the user and lab.

## Startup and migrations

`initialize_database()` is idempotent. It creates missing Phase 5 tables and adds missing columns to legacy tables without deleting data. The `schema_migrations` table is available for future versioned migrations; current upgrades are additive and safe to run at startup.

Indexes cover session resources, event chronology, finding status, objectives, and existing user/lab/session lookups.

## Reset and transactions

Reset removes session cloud events, resources, findings, objective progress, and score events, then seeds the original lab resources and records a reset event. LAB-001 remediation updates the resource and inserts `PutPublicAccessBlock` in one SQLite transaction; failures roll back both changes.

Progress is calculated from persisted objective results and session state. Completed sessions retain their score and are restored on the next login.
