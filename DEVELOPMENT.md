# Development Guide

## Local setup

1. Copy `.env.example` to `.env`.
2. Update any secret values such as `FLASK_SECRET_KEY` and `GROQ_API_KEY`.
3. Install dependencies:
   - `python -m pip install -r requirements.txt`
   - `python -m pip install pytest`
4. Start the app:
   - `python app.py`

## Application structure

- `app.py`: legacy runtime kept for compatibility with the current monolith.
- `app/`: modular foundation used for the migration path.
- `data/`: lab database fixtures and seed scripts.
- `templates/`: Flask templates used by the web UI.
- `static/`: frontend assets.

## Database notes

- SQLite is the default development database.
- The app creates and seeds the core schema during startup.
- Lab-specific command catalogs are backed by SQLite files in `data/*_lab/`.

## Validation

- Run the test suite with `python -m pytest -q`.
- Keep all server-side functionality working while moving code into the new modular layout.

## Security workflow

Phase 3 is a simulator-only security workflow. Commands create normalized cloud events, the event processor evaluates data-driven detection rules, and findings are investigated and remediated through session-scoped APIs.

For LAB-001, the supported security path is:

1. Start the lab and enumerate or inspect the S3 bucket.
2. Optionally retrieve a simulated sensitive object with `aws s3 cp`; no local filesystem is touched.
3. Review findings, evidence, resource state, related events, and the timeline.
4. Apply `aws s3api put-public-access-block --bucket cads-public-data` or the finding remediation endpoint.
5. Verify objectives and confirm the finding is `RESOLVED`.

Run Phase 3 tests with `python -m pytest -q test_phase3_security.py`. Run the full suite with `python -m pytest -q`.

The security engine does not execute shell input, contact AWS, or expose client-selected session IDs.

## Phase 4 UI

The modular factory serves the student experience at `/dashboard`, `/labs`, `/labs/<slug>`, `/progress`, and `/lab/<lab_id>`. Start the modular app with a small runner or import `create_app("development")`; the legacy `python app.py` runtime remains available for compatibility.

The UI API surface includes `/api/dashboard`, `/api/progress`, lab details, session resources, filtered events, findings, timelines, and progress. The lab workspace starts a simulator session when needed, runs only allowlisted commands, and refreshes its panels after each action. Styling lives in `static/phase4.css` and `static/phase4-catalog.css`; behavior lives in `static/phase4.js`.

For a focused UI check run `python -m pytest -q test_phase4_ui.py`. For the full suite, start the legacy server when live compatibility tests require port 5000, then run `python -m pytest -q`.

## Phase 5 accounts and persistence

Create a temporary test database with `TEST_DATABASE_URL=sqlite:///path/to/test.db` when testing account or restart behavior. The application adds missing schema columns and Phase 5 tables at startup without recreating the database.

Use `/register`, `/login`, and `/logout` for the account flow. Authenticated state-changing API calls must send `X-CSRFToken` using the token provided in the page meta tag. `test_phase5_auth.py` covers identity and CSRF; `test_phase5_persistence.py` creates a second app instance against the same database to verify restart durability.

## Phase 6 runtime

Use `python app.py` for the development server or `flask --app app:create_app run` for factory-based startup. Both use the same factory runtime. The launcher disables Flask's watchdog reloader to keep live compatibility tests stable; use an external watcher if needed.

The compatibility blueprint preserves old terminal, cheatsheet, logs, and chatbot URL contracts for existing scripts. It is not a second application. New routes and business logic belong under `app/routes/` and `app/services/`.

The complete stabilization suite is `python -m pytest -q`. Fresh/existing database startup, the canonical end-to-end smoke path, and launcher thinness are covered by `test_phase6_stabilization.py`.

## Phase 7 Multi-Lab Cloud Security Testing

Phase 7 adds comprehensive automated test suites for all 4 cloud security labs:
- `tests/test_lab002_iam.py`: Covers IAM enumeration, privilege escalation (`iam:AttachUserPolicy`), finding creation, investigation, least-privilege remediation, objective verification, restart durability, and dynamic lab reset.
- `tests/test_lab003_security_group.py`: Covers Security Group enumeration, rule inspection, ingress revocation (`0.0.0.0/0:22`), finding resolution, objective verification, restart durability, and dynamic lab reset.
- `tests/test_lab004_cloudtrail.py`: Covers CloudTrail trail discovery, event lookup and filtering, suspicious API activity detection, compromised access key deactivation, objective verification, restart durability, and dynamic lab reset.

Run the Phase 7 test suite:
```bash
python -m pytest tests/test_lab002_iam.py tests/test_lab003_security_group.py tests/test_lab004_cloudtrail.py
```

Run the complete platform test suite:
```bash
python -m pytest --ignore=test_chatbot_live.py --ignore=test_terminal_ajax.py --ignore=test_cheatsheet_integration.py --ignore=test_lab_specific_rate_limiting.py
```
