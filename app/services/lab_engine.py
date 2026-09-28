import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .cloud_provider import SimulatorProvider
from .database import get_db_connection
from .event_processor import EventProcessor


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _lab_paths():
    base = Path(__file__).resolve().parents[2]
    return [
        base / "labs" / "aws",
        base / "labs",
        base / "data" / "labs",
    ]



def load_lab_definition(slug_or_id: str):
    if slug_or_id is None:
        return None
    slug = str(slug_or_id).strip()
    if not slug:
        return None
    candidate_names = {slug, slug.replace("-", "_"), slug.replace("_", "-"), slug.upper(), slug.lower()}
    num_to_lab = {"1": "LAB-001", "2": "LAB-002", "3": "LAB-003", "4": "LAB-004"}
    if slug in num_to_lab:
        candidate_names.add(num_to_lab[slug])

    try:
        conn = get_db_connection()
        row = conn.execute("SELECT id, lab_id, slug FROM labs WHERE id = ? OR lab_id = ? OR slug = ?", (slug, slug, slug)).fetchone()
        conn.close()
        if row:
            if row["lab_id"]:
                candidate_names.add(str(row["lab_id"]))
                candidate_names.add(str(row["lab_id"]).upper())
            if row["slug"]:
                candidate_names.add(str(row["slug"]))
    except Exception:
        pass

    for folder in _lab_paths():
        if not folder.exists():
            continue
        for file in folder.rglob("*.json"):
            try:
                payload = json.loads(file.read_text(encoding="utf-8"))
            except Exception:
                continue
            p_id = str(payload.get("id", ""))
            p_slug = str(payload.get("slug", ""))
            if p_slug in candidate_names or p_id in candidate_names or p_id.upper() in candidate_names:
                if "scenario" in payload and "description" not in payload:
                    payload["description"] = payload["scenario"]
                elif "description" in payload and "scenario" not in payload:
                    payload["scenario"] = payload["description"]
                if "objectives" not in payload:
                    payload["objectives"] = []
                return payload
    return None


def create_lab_record(slug, title, description="", category="Cloud Security", difficulty="Beginner", xp=100, status="draft", metadata=None):
    metadata = metadata or {}
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO labs (slug, title, description, category, difficulty, xp, status, metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            slug,
            title,
            description,
            category,
            difficulty,
            xp,
            status,
            json.dumps(metadata),
            _utc_now(),
            _utc_now(),
        ),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def get_lab_by_slug(slug):
    lab_def = load_lab_definition(slug)
    if lab_def:
        return lab_def
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM labs WHERE slug = ? OR lab_id = ? OR id = ?", (slug, slug, slug))
        row = cur.fetchone()
        conn.close()
    except Exception:
        row = None
    if row:
        payload = dict(row)
        payload["metadata"] = json.loads(payload.get("metadata") or "{}")
        meta_id = payload.get("metadata", {}).get("lab_id") or payload.get("lab_id")
        if meta_id:
            full_def = load_lab_definition(meta_id)
            if full_def:
                return full_def
        if "description" in payload and "scenario" not in payload:
            payload["scenario"] = payload["description"]
        if "objectives" not in payload:
            payload["objectives"] = []
        return payload
    return None


def create_lab_session(user_id, lab_id, status="NOT_STARTED", metadata=None):
    session_id = f"session-{uuid.uuid4().hex}"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO lab_sessions (session_id, user_id, lab_id, started_at, status, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            user_id,
            lab_id,
            _utc_now(),
            status,
            json.dumps(metadata or {}),
        ),
    )
    conn.commit()
    conn.close()
    return session_id


def get_lab_session(session_id, db_url=None):
    conn = get_db_connection(db_url)
    cur = conn.cursor()
    cur.execute("SELECT * FROM lab_sessions WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


class LabEngine:
    def __init__(self, provider=None):
        self.provider = provider or SimulatorProvider()
        if getattr(self.provider, "_event_processor", None) is None:
            self.provider.set_event_processor(EventProcessor(self.provider))

    @property
    def event_processor(self):
        return self.provider._event_processor

    @property
    def finding_engine(self):
        return self.event_processor.finding_engine

    @property
    def db_url(self):
        return getattr(self.provider, "db_url", None)

    def load_lab(self, lab_id):
        lab = load_lab_definition(lab_id)
        if lab is None:
            raise ValueError(f"Lab {lab_id!r} not found")
        return lab

    def initialize_lab(self, lab_id):
        lab = self.load_lab(lab_id)
        return {
            "lab_id": lab["id"],
            "slug": lab["slug"],
            "title": lab["title"],
            "objectives": lab.get("objectives", []),
            "provider": lab.get("provider", "simulator"),
        }

    def _bootstrap_lab_environment(self, session_id, lab, user_id="student"):
        self.provider.reset_environment(session_id)
        for resource in lab.get("resources", []):
            self.provider.create_resource(
                session_id,
                resource["resource_type"],
                resource["resource_name"],
                region=resource.get("region", "ap-south-1"),
                configuration=resource.get("configuration", {}),
                status=resource.get("status", "ACTIVE"),
            )

        if lab.get("id") == "LAB-004" or lab.get("slug") == "cloudtrail-investigation":
            initial_events = [
                ("CloudTrail", "ConsoleLogin", "compromised-user", "IAM_USER", "SUCCESS", "MEDIUM", "compromised-user", {"login_type": "ConsolePassword", "mfa_used": False}),
                ("S3", "ListAllMyBuckets", "compromised-user", "S3_BUCKET", "SUCCESS", "LOW", "cads-confidential-bucket", {"count": 1}),
                ("S3", "GetObject", "compromised-user", "S3_OBJECT", "SUCCESS", "HIGH", "cads-confidential-bucket", {"object": "customer-pii.parquet", "classification": "SENSITIVE"}),
                ("IAM", "GetUser", "compromised-user", "IAM_USER", "SUCCESS", "MEDIUM", "compromised-user", {"user": "compromised-user"}),
                ("IAM", "AttachUserPolicy", "compromised-user", "IAM_POLICY", "SUCCESS", "HIGH", "compromised-user", {"policy_arn": "arn:aws:iam::aws:policy/AdministratorAccess", "action": "PrivilegeEscalation"}),
                ("IAM", "CreateAccessKey", "compromised-user", "IAM_USER", "SUCCESS", "HIGH", "compromised-user", {"access_key_id": "AKIAEXAMPLEROOTKEY", "status": "Active"}),
            ]
            for service, event_name, actor, r_type, outcome, severity, r_name, meta in initial_events:
                self.provider.create_event(
                    session_id,
                    service=service,
                    event_name=event_name,
                    actor=actor,
                    resource_type=r_type,
                    outcome=outcome,
                    severity=severity,
                    resource_name=r_name,
                    metadata=meta,
                    source_ip="198.51.100.99",
                )

        self.provider.create_event(
            session_id,
            "LabEngine",
            "SessionStarted",
            actor=user_id,
            resource_type="LAB",
            outcome="SUCCESS",
            severity="LOW",
            metadata={"lab_id": lab["id"], "slug": lab["slug"]},
        )

    def start_session(self, lab_id, user_id="student"):
        lab = self.load_lab(lab_id)
        catalog_id = 1
        if self.db_url:
            conn = get_db_connection(self.db_url)
            catalog = conn.execute("SELECT id FROM labs WHERE slug = ? OR lab_id = ? LIMIT 1", (lab["slug"], lab["id"])).fetchone()
            if catalog:
                catalog_id = catalog["id"]
                conn.execute("UPDATE labs SET slug = COALESCE(slug, ?), lab_id = COALESCE(lab_id, ?), title = COALESCE(title, ?), description = COALESCE(description, ?), category = COALESCE(category, ?), difficulty = COALESCE(difficulty, ?), xp = COALESCE(xp, ?), updated_at = ? WHERE id = ?", (lab["slug"], lab["id"], lab["title"], lab.get("scenario", ""), lab.get("category", "Cloud Security"), lab.get("difficulty", "Beginner"), lab.get("xp", 100), _utc_now(), catalog_id))
            else:
                cursor = conn.execute("INSERT INTO labs (slug, lab_id, title, description, category, difficulty, xp, status, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'published', ?, ?, ?)", (lab["slug"], lab["id"], lab["title"], lab.get("scenario", ""), lab.get("category", "Cloud Security"), lab.get("difficulty", "Beginner"), lab.get("xp", 100), json.dumps({"lab_id": lab["id"]}), _utc_now(), _utc_now()))
                catalog_id = cursor.lastrowid
            existing = conn.execute("SELECT session_id FROM lab_sessions WHERE user_id = ? AND lab_id = ? AND status IN ('NOT_STARTED', 'RUNNING', 'RESET') ORDER BY started_at DESC LIMIT 1", (user_id, catalog_id)).fetchone()
            if existing:
                session_id = existing["session_id"]
                conn.execute("UPDATE lab_sessions SET last_activity_at = ? WHERE session_id = ?", (_utc_now(), session_id))
                conn.commit()
                conn.close()
                if not self.provider.list_resources(session_id):
                    self._bootstrap_lab_environment(session_id, lab, user_id)
                return session_id
            conn.commit()
            conn.close()
        session_id = f"session-{uuid.uuid4().hex}"
        if self.db_url:
            conn = get_db_connection(self.db_url)
            now = _utc_now()
            conn.execute("INSERT INTO lab_sessions (session_id, user_id, lab_id, started_at, last_activity_at, status, metadata) VALUES (?, ?, ?, ?, ?, 'RUNNING', ?)", (session_id, user_id, catalog_id, now, now, json.dumps({"slug": lab["slug"], "lab_id": lab["id"]})))
            conn.commit()
            conn.close()
        self._bootstrap_lab_environment(session_id, lab, user_id)
        return session_id

    def get_lab_state(self, session_id):
        resources = self.provider.list_resources(session_id)
        events = self.provider.list_events(session_id)
        lab_id = "LAB-001"
        if self.db_url:
            conn = get_db_connection(self.db_url)
            row = conn.execute("SELECT lab_sessions.lab_id, labs.lab_id as canonical_id, labs.slug, lab_sessions.metadata FROM lab_sessions LEFT JOIN labs ON lab_sessions.lab_id = labs.id WHERE session_id = ?", (session_id,)).fetchone()
            conn.close()
            if row:
                lab_id = row["canonical_id"] or row["slug"] or row["lab_id"]
                if not lab_id and row["metadata"]:
                    try:
                        meta = json.loads(row["metadata"] or "{}")
                        lab_id = meta.get("lab_id") or meta.get("slug") or "LAB-001"
                    except Exception:
                        pass
        lab_def = load_lab_definition(lab_id)
        if lab_def:
            lab_id = lab_def["id"]
        return {
            "session_id": session_id,
            "lab_id": lab_id,
            "status": "active",
            "resources": resources,
            "event_count": len(events),
            "events": events,
            "findings": self.finding_engine.list_findings(session_id),
        }

    def check_objectives(self, session_id):
        from .verification_engine import verify_objectives

        results = verify_objectives(session_id, self.provider)
        if self.db_url:
            conn = get_db_connection(self.db_url)
            now = _utc_now()
            for objective_id, result in results.items():
                status = "COMPLETED" if result["status"] == "PASS" else "PENDING"
                conn.execute("INSERT INTO objective_progress (session_id, objective_id, status, completed_at, evidence) VALUES (?, ?, ?, ?, ?) ON CONFLICT(session_id, objective_id) DO UPDATE SET status = excluded.status, completed_at = excluded.completed_at, evidence = excluded.evidence", (session_id, objective_id, status, now if status == "COMPLETED" else None, json.dumps(result)))
            conn.execute("UPDATE lab_sessions SET last_activity_at = ? WHERE session_id = ?", (now, session_id))
            conn.commit()
            conn.close()
        return results

    def record_activity(self, session_id):
        if not self.db_url:
            return
        conn = get_db_connection(self.db_url)
        conn.execute("UPDATE lab_sessions SET commands_executed = COALESCE(commands_executed, 0) + 1, last_activity_at = ? WHERE session_id = ?", (_utc_now(), session_id))
        conn.commit()
        conn.close()

    def complete_lab(self, session_id):
        summary = self.check_objectives(session_id)
        final_pass = all(result.get("status") == "PASS" for result in summary.values())
        if self.db_url and final_pass:
            conn = get_db_connection(self.db_url)
            now = _utc_now()
            conn.execute("UPDATE lab_sessions SET status = 'COMPLETED', completed_at = ?, last_activity_at = ?, score = 100 WHERE session_id = ?", (now, now, session_id))
            conn.execute("INSERT INTO score_events (session_id, event_type, points, timestamp, metadata) SELECT ?, 'LAB_COMPLETED', 100, ?, '{}' WHERE NOT EXISTS (SELECT 1 FROM score_events WHERE session_id = ? AND event_type = 'LAB_COMPLETED')", (session_id, now, session_id))
            conn.commit()
            conn.close()
        return {
            "status": "completed" if final_pass else "ready",
            "session_id": session_id,
            "objectives": summary,
        }

    def reset_lab(self, session_id):
        lab_identifier = "LAB-001"
        if self.db_url:
            conn = get_db_connection(self.db_url)
            row = conn.execute("SELECT labs.lab_id, labs.slug, lab_sessions.metadata FROM lab_sessions LEFT JOIN labs ON lab_sessions.lab_id = labs.id WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                lab_identifier = row["lab_id"] or row["slug"]
                if not lab_identifier and row["metadata"]:
                    try:
                        meta = json.loads(row["metadata"] or "{}")
                        lab_identifier = meta.get("lab_id") or meta.get("slug") or "LAB-001"
                    except Exception:
                        pass
            conn.execute("DELETE FROM objective_progress WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM score_events WHERE session_id = ?", (session_id,))
            conn.execute("UPDATE lab_sessions SET status = 'RESET', completed_at = NULL, score = 0, last_activity_at = ? WHERE session_id = ?", (_utc_now(), session_id))
            conn.commit()
            conn.close()
        lab = self.load_lab(lab_identifier or "LAB-001")
        self._bootstrap_lab_environment(session_id, lab, "student")
        self.provider.create_event(
            session_id,
            "LabEngine",
            "LabReset",
            actor="student",
            resource_type="LAB",
            outcome="SUCCESS",
            severity="LOW",
            metadata={"lab_id": lab["id"]},
        )
        return {"status": "reset", "session_id": session_id, "lab_id": lab["id"]}
