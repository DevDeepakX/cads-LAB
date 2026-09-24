# CADS — Cloud Attack-Defense Simulation Platform

**CADS (Cloud Attack-Defense Simulation)** is an interactive, secure, and production-grade Cloud Security Learning and Attack-Defense Simulation Platform designed for hands-on cybersecurity education, offensive security exploration, cloud detection engineering, and incident response.

---

## Key Features

- **Realistic Multi-Domain Cloud Curriculum:** Hands-on labs covering AWS S3 (Storage Security), IAM (Identity Security & Privilege Escalation), EC2/VPC (Network Security & Security Groups), and CloudTrail (Threat Detection & Incident Response).
- **Safe Deterministic Cloud Simulator:** Zero arbitrary shell or subprocess execution (`eval()`, `exec()`, `shell=True`, or `os.system()` are completely absent). All interactions run against a deterministic, session-scoped cloud state machine.
- **No Real AWS Credentials Required:** 100% simulated in-memory and persistent SQLite cloud resource environment — safe for classroom, enterprise, and competitive training without cloud billing or accidental exposure.
- **Event-Driven Detection Engine:** Real-time stream processing of cloud API calls evaluating data-driven detection rules to surface alerts, risk scoring, and evidence artifacts.
- **Structured Finding Lifecycle & Incident Response:** Complete investigation workflows tracking findings from `OPEN` to `INVESTIGATING` to `RESOLVED` with 1-click or CLI-based remediation actions.
- **Session & Identity Isolation:** Robust multi-user isolation with hashed authentication, CSRF protection, persistent lab sessions, dynamic resets, and restart recovery.

---

## Lab Curriculum

| Lab ID | Lab Name | Cloud Service | Category | Difficulty | Focus Area |
| --- | --- | --- | --- | --- | --- |
| **LAB-001** | Public S3 Bucket Discovery & Hardening | Amazon S3 | Storage Security | Beginner | Unauthenticated read exposure, sensitive data exfiltration, PublicAccessBlock |
| **LAB-002** | Excessive IAM Permissions & Privilege Escalation | AWS IAM | IAM Security | Intermediate | Attached user policies, wildcard permissions, AdministratorAccess escalation |
| **LAB-003** | Insecure Security Group Remediation | Amazon EC2 / VPC | Network Security | Beginner | Ingress CIDR inspection, open SSH (0.0.0.0/0:22) exposure, firewall hardening |
| **LAB-004** | CloudTrail Threat Investigation & Response | AWS CloudTrail | Threat Detection & IR | Intermediate | Audit log queries, anomalous reconnaissance, compromised access key deactivation |

*See [`docs/LAB_CURRICULUM.md`](file:///c:/Users/garag/OneDrive/Desktop/project/CADS%20LAB/cads-LAB/docs/LAB_CURRICULUM.md) for full curriculum specifications.*

---

## Architecture Overview

```
                          ┌──────────────────────────┐
                          │   Flask App Factory      │
                          │   (Blueprints & Auth)    │
                          └─────────────┬────────────┘
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                      ▼
        ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
        │  Command Engine  │  │  Event Pipeline  │  │ Finding Service  │
        │  (Safe / Parsed) │  │  & Detection     │  │ (Investigation)  │
        └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
                 │                      │                      │
                 └──────────────────────┼──────────────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────┐
                          │    Cloud Simulator &     │
                          │  Session-Scoped SQLite   │
                          └──────────────────────────┘
```

---

## Quick Start

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- pip / virtualenv

### 2. Setup
```bash
# Clone and enter directory
cd cads-LAB

# Copy configuration
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
pip install pytest
```

### 3. Run Application
```bash
# Start CADS platform
python app.py
```
Visit `http://127.0.0.1:5000` in your web browser.

### 4. Run Test Suite
```bash
# Run full automated test suite
python -m pytest --ignore=test_chatbot_live.py --ignore=test_terminal_ajax.py --ignore=test_cheatsheet_integration.py --ignore=test_lab_specific_rate_limiting.py
```

---

## Documentation

- [Lab Curriculum](file:///c:/Users/garag/OneDrive/Desktop/project/CADS%20LAB/cads-LAB/docs/LAB_CURRICULUM.md) — Detailed lab guides, learning objectives, and lifecycle workflows.
- [Architecture](file:///c:/Users/garag/OneDrive/Desktop/project/CADS%20LAB/cads-LAB/ARCHITECTURE.md) — System design, service boundaries, and security model.
- [Detection Rules](file:///c:/Users/garag/OneDrive/Desktop/project/CADS%20LAB/cads-LAB/docs/DETECTION_RULES.md) — Security detection rules, severities, and finding triggers.
- [Security Event Model](file:///c:/Users/garag/OneDrive/Desktop/project/CADS%20LAB/cads-LAB/docs/SECURITY_EVENT_MODEL.md) — Normalized event telemetry schema.
- [Development Guide](file:///c:/Users/garag/OneDrive/Desktop/project/CADS%20LAB/cads-LAB/DEVELOPMENT.md) — Local development and verification procedures.