# CADS Architecture Audit

## 1. Executive Summary

CADS is currently a working Flask-based simulation lab for cloud and cyber security training, but it is not yet organized as a product-grade cloud security learning platform. The repository has a viable core:

- Flask application and lab flow exist
- Terminal simulation is implemented
- Browser-based lab UI exists
- S3-focused lab data and simulated command logic exist
- Chatbot and helper APIs are in place
- Logs and session-state persistence exist
- A test suite and multiple lab datasets exist

However, the app is still a single-file monolith (`app.py`) with business logic, routes, simulator behavior, logging, AI integration, and scoring all mixed together. It also still uses broad generic cyber-style language and educational patterns rather than a cloud-first product identity.

This means the project has strong reusable foundations, but it needs a deliberate architectural refactor and product redesign before it can become a serious cloud security training platform.

---

## 2. Repository Overview

### Main project layout

Current repository structure shows a compact lab project with:

- Root Flask app: `app.py`
- HTML templates under `templates/`
- Static CSS/JS under `static/`
- Lab datasets under `data/`
- Logs under `logs/`
- Generated database files: `database.db` and several lab SQLite databases
- Utility scripts and test scripts in the project root

### Current intent

The project was built as a cybersecurity training simulator with:

- terminal-style interactions
- S3 reconnaissance and file access scenarios
- attack/defense mode switching
- AI-assisted guidance via Groq API
- mock cloud command execution and response simulation
- session logging and scoring

This is useful, but the product goal described in the brief is more ambitious: it must become a structured, cloud-native, secure training platform focused on AWS and cloud security education.

---

## 3. Existing Architecture

### 3.1 Application type

The project is a Flask web app using:

- Flask routes
- server-side session state
- SQLite databases
- JSON-based lab definitions
- templates for UI rendering
- lightweight AJAX endpoints for terminal and API actions

The main entry point is a single file: `app.py`.

### 3.2 Core architectural shape

The application currently follows a hybrid pattern:

- `app.py` contains:
  - Flask app initialization
  - environment setup
  - database setup
  - route definitions
  - lab flow logic
  - terminal logic
  - command patterns and output simulation
  - log generation
  - chatbot logic
  - scoring / progress tracking
  - reset logic
  - news scheduler logic

This results in a monolithic architecture where business logic, interface rendering, simulator logic, and data access are all colocated.

### 3.3 Database usage

There are multiple SQLite databases, including:

- root `database.db`
- `data/open_s3_lab/open_s3_lab.db`
- `data/network_recon_lab/network_recon_lab.db`
- `data/pwndora_lab/pwndora_lab.db`

The app uses SQLite in several ways:

- generic app metadata (`labs`, `tasks`, `progress`)
- lab-specific command tables (`attack_commands`, `defense_commands`)
- lab execution tracking (`actions`, `attack_executions`, `defense_executions`)
- per-session JSON logs under `logs/`

The structure is functional but not normalized enough for a multi-lab, multi-user, product-grade platform.

### 3.4 Frontend architecture

The frontend is built from HTML templates and CSS/JS assets:

- `templates/index.html`
- `templates/labs.html`
- `templates/lab_intro.html`
- `templates/lab_mode_select.html`
- `templates/lab_tasks.html`
- `templates/terminal.html`
- `templates/result.html`
- `templates/logs.html`
- `templates/_chatbot.html`

CSS is defined in `static/style.css` with lots of neon cyber styling and custom gradients, but it is not yet organized into a component system or product UI library.

The frontend also contains a floating chatbot widget and terminal-driven interactions.

### 3.5 Lab model

The current lab model is driven partly by `data/labs.json`, which defines:

- lab metadata
- modes
- attack tasks
- defense tasks
- command lists
- flags metadata

This makes the project partially data-driven already, which is a good reusable foundation for a scalable lab system.

### 3.6 Terminal implementation

The terminal logic is one of the strongest reusable components in the project.

It includes:

- command parsing and responder logic
- command recognition patterns
- structured fake cloud outputs for AWS CLI commands
- simulated linux/network commands
- state transitions (`initialized`, `recon`, `attack_started`, `mitigation_applied`)
- AI analysis calls after command execution

This is useful and should be retained, but it needs to be refactored into a proper command engine with allowlisting and lab-specific resource simulation.

### 3.7 Chatbot implementation

The chatbot is implemented as:

- Flask endpoint `/chatbot_api`
- Groq API integration
- fallback local response logic
- dataset-informed context injection
- optional image input support

This is a strong base for the future AI Cloud Security Assistant, but today it is still more of a general-purpose lab assistant than a guided cloud-security tutor.

### 3.8 Logs implementation

The project logs session events in JSON files under `logs/` and also records some lab actions in database tables.

Current behavior:

- each session creates a log file
- actions are appended to JSON
- event data includes timestamps, source IP, action, description
- terminal actions also write to `attack_executions` and `defense_executions`

This is useful for timeline and forensics work but is not yet standardized into a cloud event schema or normalized model.

---

## 4. Current Features

### Included features

The repository currently includes:

- landing dashboard
- lab catalog and mode selection
- terminal lab gameplay
- attack-mode and defense-mode flow
- task system with answers and hints
- static lab JSON definitions
- simulated AWS S3, network, and PwnDora-style scenarios
- AI chatbot integration
- command lookup and hint service
- logs and timeline output
- basic score tracking with database persistence
- reset functionality
- test scripts for command logic and chatbot behavior

### Existing lab themes

The current active concept includes:

- S3 bucket exposure lab
- network recon lab
- PwnDora-style challenge
- generic attack/defense learning loops

This is a good base for the required cloud-security transformation, but the current scope is not cloud-first enough and not yet aligned with AWS-centric learning paths.

---

## 5. Reusable Components

The following components can be reused and redeveloped rather than discarded:

### 5.1 Flask app shell

The app itself is usable as a launch point for a reorganized product architecture.

### 5.2 Lab routing and lab selection flow

The current `/lab/<lab_id>` and `/lab/<lab_id>/start` patterns are a useful foundation for a proper lab engine.

### 5.3 Terminal simulator

This is one of the strongest reusable components. It can be adapted into a controlled cloud terminal with allowlisted commands and an event engine.

### 5.4 `data/labs.json`

This file is a valuable starting point for lab metadata, task definitions, and data-driven lab scaffolding.

### 5.5 Multi-database approach

The use of database files per lab is useful for isolated training environments. It can evolve into a cleaner lab resource model.

### 5.6 Chatbot API layer

The current chatbot can be repurposed into a guided cloud-security tutor that provides hints, investigation guidance, and defense advice without revealing flags.

### 5.7 Log creation mechanism

Session logs and event generation can become the basis for the Cloud SOC, Timeline, and Forensics sections.

### 5.8 Test infrastructure

There are already tests for command and chatbot flows, which can be upgraded into a proper unit and integration suite.

---

## 6. Problems and Architectural Debt

### 6.1 Monolithic design

The biggest problem is that all responsibilities live inside `app.py`:

- UI
- database access
- business logic
- terminal simulation
- AI calls
- event generation
- security assumptions
- flow control

This makes the project hard to extend, hard to secure, and hard to validate.

### 6.2 Cloud security product mismatch

The project still reads like a generic cybersecurity lab. It is not yet shaped around:

- AWS and cloud security learning paths
- IAM, S3, EC2, VPC, CloudTrail, GuardDuty, KMS, Secrets Manager
- attack path modeling and defense verification
- cloud SOC workflows
- incident response and forensics
- cloud posture scoring and policy checks

### 6.3 Hardcoded logic and low abstraction

Many behaviors are directly embedded in route handlers and terminal command matching instead of being modeled as services.

Examples:

- route-level state mutation
- direct string-based command detection
- hardcoded AWS outputs
- event generation effectively embedded in routes
- scoring logic in route handlers
- limited separation between attack and defense logic

### 6.4 Security weakness in the current app

This is the most important concern for a cybersecurity app itself.

Current issues include:

- hardcoded Flask secret key
- no real authentication/authorization model
- no CSRF protection
- no role separation for admin functions
- no proper input validation or sanitization in most flows
- no secure cookie settings
- no environment-based configuration management
- allowlist not enforced at the app architecture level
- direct use of web-session state for security-critical flows
- no audit trail model for user actions and lab actor identity
- arbitrary command simulation is not separated from a secure cloud-policy engine

### 6.5 Weak data model / schema design

The app uses SQLite tables but not a coherent domain model.

Current weaknesses:

- no normalized user model
- no lab resource model
- no lab session model with objective states
- no findings model
- no unified event schema
- no data-driven verification framework
- no reusable scoring events table
- no clear differentiation between user state and lab state

### 6.6 Test and validation gaps

The test files exist, but they are still largely script-like checks rather than a coherent test framework for the platform vision.

### 6.7 UX mismatch

The current frontend is visually strong but still feels like a generic cyber-themed prototype rather than a serious cloud security training product.

Current UX problems:

- neon-heavy styling and generic cyber aesthetics
- the homepage is not truly positioned as a cloud security training platform
- concept labeling is broader than the intended product scope
- lab experience lacks a strong SOC / cloud operations workflow
- the dashboard is missing the required product-language: progress, streak, learning paths, posture, leaderboard, achievements, SOC center, and attack/defense workflow

---

## 7. Security Issues to Address

The project is itself a cyber security platform, so its own security model must be stronger than the current implementation.

### Immediate risks

1. Hardcoded secret key
2. No real authentication
3. No admin separation
4. No CSRF enforcement
5. Session data is used as the primary state machine without hardened validation
6. API endpoints are not structured around role and lab ownership checks
7. No allowlist for cloud commands and actions
8. No lab-isolated resource containers
9. No audit or immutable action log model
10. No environment variable requirement for secrets and config

### Required future controls

- secure password hashing
- session hardening
- secure cookies
- rate limiting
- input validation
- authorization checks per lab session
- admin-only operations
- configuration via `.env.example` and environment variables
- audit logging for all user actions
- explicit command allowlisting
- no unsafe shell execution through the web app

---

## 8. Technical Debt

This project has technical debt in several layers:

- route-heavy file organization
- duplicate and partially obsolete files in the root
- multiple versions of similar scripts and documentation
- hardcoded outputs and synthetic command logic
- unclear separation of app logic and lab content
- inconsistent naming and concept scope
- generic cyber training vocabulary instead of cloud security vocabulary
- lack of a shared event schema across the lab engine
- limited support for future AWS sandbox integration

### Obsolete or duplicate files

The repository includes several documentation and helper files that are not yet clearly organized:

- `README.md`, `README.txt`, `README_CHATBOT.md`
- multiple chatbot summary and diagnostic files
- `demo_fixes.py`, `diagnose_chatbot.py`, `check_setup.py`
- multiple lab verification and monitor scripts
- multiple `seed_*.py` scripts and database artifacts

These can be useful, but they should be organized into `docs/`, `scripts/`, and `tests/` once the new architecture is implemented.

---

## 9. UX Issues

The product has potential, but the current UX is inconsistent with the target identity.

### Current issues

- The homepage calls it a generic cyber lab instead of a cloud security product
- Styling is aggressive and neon-heavy
- Product language is not oriented around learning paths, progression, SOC workflows, and cloud posture
- Attack/defense switching lacks a polished platform feel
- There is no coherent dashboard showing learning progress, achievements, or posture across a cloud security curriculum
- The lab page needs a stronger structure: left instructions, center terminal, right resource explorer, bottom evidence/timeline/hints
- There is no unified cloud attack graph, SOC dashboard, or cloud forensics interface yet

---

## 10. Proposed Architecture

The project should move to a modular architecture that preserves useful pieces but introduces domain boundaries.

### Target architecture

```text
cads-LAB/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── labs.py
│   │   ├── terminal.py
│   │   ├── attack.py
│   │   ├── defense.py
│   │   ├── soc.py
│   │   ├── forensics.py
│   │   ├── api.py
│   │   └── admin.py
│   ├── services/
│   │   ├── lab_engine.py
│   │   ├── command_engine.py
│   │   ├── event_engine.py
│   │   ├── scoring_engine.py
│   │   ├── verification_engine.py
│   │   ├── hint_engine.py
│   │   ├── finding_engine.py
│   │   ├── attack_path_engine.py
│   │   └── cloud_simulator.py
│   ├── models/
│   │   ├── user.py
│   │   ├── lab.py
│   │   ├── session.py
│   │   ├── finding.py
│   │   └── event.py
│   ├── security/
│   │   ├── auth.py
│   │   ├── csrf.py
│   │   ├── rate_limit.py
│   │   └── command_allowlist.py
│   ├── utils/
│   │   ├── time.py
│   │   ├── json.py
│   │   └── cloud_helpers.py
│   └── providers/
│       ├── base.py
│       ├── simulator.py
│       └── aws.py
├── labs/
│   ├── aws/
│   │   ├── iam/
│   │   ├── s3/
│   │   ├── ec2/
│   │   ├── vpc/
│   │   ├── logging/
│   │   ├── secrets/
│   │   ├── containers/
│   │   └── serverless/
│   └── shared/
│       ├── lab.yaml
│       ├── validation.yaml
│       ├── hints.yaml
│       └── solution.md
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── assets/
├── tests/
├── docs/
├── scripts/
├── migrations/
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── README.md
├── SECURITY.md
├── ARCHITECTURE.md
├── LAB_AUTHORING_GUIDE.md
├── CLOUD_SIMULATOR.md
├── API.md
├── DEVELOPMENT.md
├── DEPLOYMENT.md
├── ROADMAP.md
└── CONTRIBUTING.md
```

### Core principles for the new architecture

- cloud-first product identity
- data-driven lab definitions
- modular services with explicit responsibilities
- simulator-first implementation
- clean event schema
- maintainable security boundary
- lab isolation for each student session
- extensibility for real AWS sandbox later

---

## 11. Migration Plan

### Phase 1 — Repository audit and foundation

Goal: stabilize and organize the project.

Actions:

- keep the useful Flask app shell
- document the current architecture
- create the new project package structure
- separate app config and environment settings
- begin moving data schemas into clean model boundaries

### Phase 2 — Authentication and user account model

Actions:

- implement secure user registration/login
- use hashed passwords
- add session hardening
- add admin role handling
- set secure cookies and CSRF protection

### Phase 3 — Dashboard and lab catalog

Actions:

- redesignlanding/dashboard for cloud security product identity
- create learning paths
- create a new lab catalog with categories, difficulty, and progress states
- link completion to user progress data

### Phase 4 — Lab engine and session model

Actions:

- formalize `lab_sessions`, `user_progress`, `lab_objects`, `flags`, `hints`
- add objective lifecycle tracking
- maintain lab state and session state safely
- add reset flow with confirmation

### Phase 5 — Cloud simulator and command engine

Actions:

- build a command allowlist engine
- define a cloud event schema
- map actions to IAM/S3/EC2/VPC events
- create structured outputs and deterministic lab states

### Phase 6 — Attack / Defense / Verification

Actions:

- standardize attack objectives
- standardize defense verification
- add flag generation and validation engine
- implement scoring with event logging

### Phase 7 — SOC / Forensics / Timeline / Attack path

Actions:

- produce event timeline screens
- create detection findings model
- create forensics investigation interfaces
- add attack path graph or diagram view

### Phase 8 — Knowledge base / AI assistant / admin lab builder

Actions:

- add knowledge base entries for cloud concepts
- redesign the chatbot as a guided learning assistant
- add admin tooling for creating labs and validation rules

### Phase 9 — Testing and hardening

Actions:

- unit test the service layer
- add API tests
- add integration tests for the five priority labs
- verify security controls and command restrictions

### Phase 10 — Deployment readiness

Actions:

- Docker setup
- docs and deployment flow
- production configuration checks
- sandbox-ready AWS abstraction for future real cloud integration

---

## 12. Recommended Strategy for This Repository

The right move is not a full rewrite from scratch. The right move is to preserve the useful foundation and refactor it deliberately.

### Keep

- the Flask app shell
- the lab flow concept
- terminal-based learning loop
- data-driven lab metadata in JSON
- command-response simulation logic
- AI assistant infrastructure
- log generation pattern
- test scripts as an early seed

### Refactor

- move logic into services and models
- standardize database schema
- centralize event generation and verification
- redesign the frontend for cloud-security product identity
- apply security controls and proper config management
- convert lab-centric logic into a lab engine and validation engine

### Remove or de-emphasize

- generic cyber references not relevant to cloud security
- neon-heavy styling not aligned with a professional SOC product
- oversized root folder clutter and duplicate docs
- hardcoded app secret and insecure patterns
- unstructured app.py logic
- low-value or duplicate helper scripts after migration

---

## 13. Final Assessment

CADS already has a good prototype foundation, especially in lab flow, terminal simulation, command knowledge, and chatbot infrastructure. That is valuable.

However, the current repository is best described as a functional cybersecurity lab prototype rather than a cloud security training platform product. The codebase needs:

- product architecture
- cloud-first domain model
- security hardening
- modular service boundaries
- data-driven lab execution
- stronger SOC/forensics features
- modern professional UI
- proper developer and user documentation

The recommendation is to proceed carefully: keep the working behaviors, refactor the architecture, and build the cloud security platform incrementally around the existing learning loop.

---

## 14. Phase 1 Recommendation

The first implementation phase should be:

1. create the modular project structure
2. define the core models and schemas
3. refactor `app.py` into app packages and routes
4. establish a secure config and environment model
5. create a unified cloud event engine and verification engine
6. prepare the five priority labs as the vertical slice

This is the correct next step before building out the full platform.
