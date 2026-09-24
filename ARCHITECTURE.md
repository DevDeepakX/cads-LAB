# CADS Lab Architecture

## Overview

This repository is being migrated from a single-file Flask monolith into a modular foundation that preserves the current application behavior while making future platform work safer and more testable.

## Current state

- Primary entry point: `app.py` remains the legacy runtime for compatibility.
- New foundation package: `app/`
  - `app/__init__.py`: Flask application factory entry point
  - `app/config.py`: environment-driven configuration
  - `app/routes/`: blueprint-based route modules
  - `app/services/`: database, lab, command, scoring, and simulator services
  - `app/models/`: data models for labs and sessions
  - `app/security/`: validation and access logic
- Local persistence: SQLite for development, with configuration via environment variables.

## Design goals for Phase 1

1. Keep the existing app running while introducing modular structure.
2. Centralize configuration in environment variables and `.env.example`.
3. Create a database foundation with reusable schema helpers.
4. Move core logic toward app factory and service-layer patterns without forcing a full rewrite.
5. Preserve backward compatibility with legacy routes and templates during migration.

## Phase 3 security engine

The simulator now processes every normalized cloud event through an event processor. The processor evaluates data-driven rules from `app/services/detection_engine.py` and stores session-scoped findings in `app/services/finding_engine.py`.

The security flow is:

`command -> simulator resource/event -> event processor -> detection rule -> finding -> investigation -> defense event -> re-evaluation -> verification`

Findings retain evidence, affected resource, timestamps, recommendation, and lifecycle status (`OPEN`, `INVESTIGATING`, `RESOLVED`). `InvestigationService` exposes related resources, events, evidence, and chronological timelines. `DefenseEngine` performs explicit simulated remediation and emits its own cloud event.

The Flask factory creates one `SimulatorProvider` per application and injects it into the lab, command, investigation, and defense services. APIs use the server-side Flask lab session; clients cannot select an arbitrary session ID.

Phase 3 deliberately excludes dashboards, gamification, AI, real AWS integration, and broad lab expansion.

## Phase 4 student experience

The factory-backed UI uses a shared shell in `templates/phase4_base.html` with a focused sidebar, simulation status bar, responsive panels, and one visual language. The dashboard, catalog, overview, progress page, and lab workspace are rendered by Flask and hydrate from session-scoped JSON APIs in `app/routes/dashboard.py` and `app/routes/labs.py`.

The workspace keeps objectives, the safe simulator terminal, resources, findings, telemetry, and timeline together. `static/phase4.js` performs lightweight request-driven refreshes after commands and remediation; it does not invent activity or statistics. Resource and finding details are revealed from the backend response so investigation remains part of the lab.

Phase 4 adds no dashboard persistence, WebSockets, AI, leaderboard, achievements, or real cloud integration.

## Phase 5 identity and persistence

The Flask factory passes its configured SQLite URL into the simulator provider and finding engine. Persistent records are owned through `users -> lab_sessions`; resources, events, findings, objective progress, and score events all use the session ID as their boundary. Login restores the user's latest session, including completed sessions for dashboard progress.

Authentication uses Werkzeug password hashes, signed Flask sessions, and one session-bound CSRF token. Student APIs resolve the authenticated user server-side and reject session records owned by another user. LAB-001 remediation commits resource hardening and its cloud event transactionally.

## Phase 6 runtime authority

`app.create_app()` is the only application implementation. The root `app.py` file is a launcher that imports the factory-created application. Legacy URLs still used by compatibility scripts are registered through `app/compatibility.py`; they do not own separate startup, database, session, or business logic.

Database startup uses additive, idempotent schema reconciliation and records the honest baseline plus Phase 5 and Phase 6 versions in `schema_migrations`. See `docs/DATABASE_MIGRATIONS.md` and `docs/LEGACY_RUNTIME_MIGRATION.md` for boundaries and rollback limitations.

## Phase 7 cloud security lab expansion

The platform expands from a single S3 bucket lab into a multi-domain Cloud Security Learning and Attack-Defense Simulation Platform supporting 4 distinct core labs:
- **LAB-001 (Storage Security):** Public S3 Bucket Discovery & Hardening
- **LAB-002 (IAM Security):** Excessive IAM Permissions & Privilege Escalation
- **LAB-003 (Network Security):** Insecure Security Group Remediation (Port 22 SSH Ingress)
- **LAB-004 (Threat Detection & Incident Response):** CloudTrail Investigation & Compromised Identity Revocation

### Architecture Components in Phase 7:
1. **Dynamic Lab Loader:** `app/services/lab_engine.py` dynamically loads lab metadata, objective verifiers, and seed states across `data/labs/*.json` and `labs/aws/*/*.json`.
2. **Deterministic Safe Command Dispatcher:** Expanded `app/services/command_engine.py` and `app/services/cloud_simulator.py` supporting `iam`, `ec2`, `cloudtrail`, and `s3` commands with zero shell execution.
3. **Multi-Domain Detection Engine:** Evaluates declarative detection rules (`S3-PUBLIC-ACCESS`, `IAM-PRIVILEGE-ESCALATION`, `EC2-OPEN-SSH`, `CLOUDTRAIL-SUSPICIOUS-ACTIVITY`) extracting real-time evidence artifacts.
4. **Remediation & Defense Pipeline:** Dynamic `DefenseEngine` and `EventProcessor.reevaluate` supporting S3 bucket hardening, IAM policy modification, Security Group ingress revocation, and Access Key deactivation.
5. **Session-Bound Persistence & Multi-Lab Isolation:** Per-user, per-lab session isolation with full restart recovery and dynamic state reset.

