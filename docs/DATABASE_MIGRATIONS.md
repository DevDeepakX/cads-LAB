# Database Migrations

## Current mechanism

CADS uses the existing SQLite startup migration mechanism in `app/services/database.py`. It is intentionally additive and idempotent rather than Alembic-based because the repository has no established migration runner and currently supports one local SQLite deployment model.

Every factory startup:

1. Opens the configured `DATABASE_URL`.
2. Creates missing core and Phase 5 tables.
3. Adds missing compatibility columns to legacy tables.
4. Creates targeted indexes.
5. Records schema versions in `schema_migrations`.

## Schema versions

The repository did not contain historical migration records before Phase 6. The baseline is recorded honestly as:

- `000_baseline_unversioned`: pre-Phase 6 database state; exact historical ordering is unavailable.
- `001_phase5_persistence`: persistent users, sessions, resources, events, findings, objectives, and scores.
- `002_phase6_runtime_stability`: version recording, legacy schema reconciliation, indexes, and stable startup behavior.

Versions are inserted with `INSERT OR IGNORE`, so repeated startup is safe.

## Compatibility and rollback

Legacy tables are not deleted. Missing columns such as `labs.slug`, `labs.lab_id`, user activity fields, event identifiers, and finding evidence are added in place. Existing rows remain available to compatibility routes and the modular services.

The current mechanism has no automatic rollback or down migrations. A failed startup migration raises an error before the application serves requests; transaction boundaries protect each initialization run. A formal migration runner should be introduced when the project adds multiple deployment environments or irreversible schema changes.

Fresh database startup and existing Phase 5 database startup are covered by `test_phase6_stabilization.py`.
