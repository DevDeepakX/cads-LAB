# Legacy Runtime Migration

Phase 6 makes the application factory the only authoritative Flask runtime. `app.py` is now a thin launcher and contains no route registration or business logic.

| Legacy component | Authoritative component | Status |
| --- | --- | --- |
| Flask startup and configuration | `app.create_app()` and `app/config.py` | Migrated |
| Core database initialization | `app/services/database.py` | Migrated and versioned |
| Cloud resources and events | `SimulatorProvider` and `CloudEvent` persistence | Migrated |
| Detection and findings | `EventProcessor`, `DetectionEngine`, `FindingEngine` | Migrated |
| Authentication and ownership | `app/routes/auth.py`, `app/security/auth.py` | Migrated |
| LAB-001 start, state, reset, verification | `app/routes/labs.py`, `LabEngine` | Migrated |
| Dashboard and student UI | Factory blueprints and Phase 4 templates | Migrated |
| Legacy start URLs, terminal AJAX, logs, cheatsheet rate limit | `app/compatibility.py` | Compatibility adapter |
| Legacy chatbot URL and local fallback | `app/compatibility.py` | Compatibility adapter |
| Legacy lab-specific command catalogs | Existing data files and compatibility URL contracts | Deprecated, compatibility-only |
| Legacy live-news scheduler and Groq assistant implementation | No factory equivalent | Deprecated and intentionally not part of the authoritative runtime |

Compatibility routes preserve old smoke scripts and URLs, but they are registered by `create_app()` and do not create a second Flask app. New platform behavior must be added to modular blueprints and services.

The compatibility layer is intentionally narrow. It does not restore the old random defense bot, anonymous legacy session model, duplicate terminal dispatcher, or separate lab database initialization.
