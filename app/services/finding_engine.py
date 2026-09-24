import json
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from .database import get_db_connection


class FindingEngine:
    """Session-scoped in-memory findings for the simulator security layer."""

    def __init__(self, db_url=None):
        self._findings = {}
        self.db_url = db_url

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def create_or_update(self, session_id, detection):
        key = (session_id, detection["rule_id"], detection.get("resource_id"))
        now = self._now()
        if self.db_url:
            conn = get_db_connection(self.db_url)
            finding = conn.execute("SELECT * FROM findings WHERE session_id = ? AND rule_id = ? AND resource_id IS ?", (session_id, detection["rule_id"], detection.get("resource_id"))).fetchone()
            if finding:
                conn.execute("UPDATE findings SET last_seen = ?, updated_at = ?, evidence = ?, status = CASE WHEN status = 'RESOLVED' THEN 'OPEN' ELSE status END WHERE id = ?", (now, now, json.dumps(detection.get("evidence", [])), finding["id"]))
                conn.commit()
                updated = conn.execute("SELECT * FROM findings WHERE id = ?", (finding["id"],)).fetchone()
                conn.close()
                return self._from_row(updated)
            finding_id = f"finding-{uuid4().hex}"
            conn.execute("INSERT INTO findings (finding_id, session_id, rule_id, title, severity, status, source, service, resource_id, description, evidence, recommendation, first_seen, last_seen, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (finding_id, session_id, detection["rule_id"], detection["title"], detection["severity"], detection["rule_id"], detection["service"], detection.get("resource_id"), detection["description"], json.dumps(detection.get("evidence", [])), detection.get("recommendation", ""), now, now, now, now))
            conn.commit()
            created = conn.execute("SELECT * FROM findings WHERE finding_id = ?", (finding_id,)).fetchone()
            conn.close()
            return self._from_row(created)
        finding = self._findings.get(key)
        if finding:
            finding["last_seen"] = now
            finding["updated_at"] = now
            finding["evidence"] = detection.get("evidence", finding["evidence"])
            if finding["status"] == "RESOLVED":
                finding["status"] = "OPEN"
            return deepcopy(finding)

        finding = {
            "finding_id": f"finding-{uuid4().hex}",
            "session_id": session_id,
            "rule_id": detection["rule_id"],
            "title": detection["title"],
            "description": detection["description"],
            "severity": detection["severity"],
            "service": detection["service"],
            "resource_id": detection.get("resource_id"),
            "status": "OPEN",
            "first_seen": now,
            "last_seen": now,
            "evidence": detection.get("evidence", []),
            "recommendation": detection.get("recommendation", "Investigate and remediate the affected resource."),
            "created_at": now,
            "updated_at": now,
        }
        self._findings[key] = finding
        return deepcopy(finding)

    def list_findings(self, session_id):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            rows = conn.execute("SELECT * FROM findings WHERE session_id = ? ORDER BY created_at, id", (session_id,)).fetchall()
            conn.close()
            return [self._from_row(row) for row in rows]
        return [deepcopy(item) for (sid, _rule, _resource), item in self._findings.items() if sid == session_id]

    def get_finding(self, session_id, finding_id):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            row = conn.execute("SELECT * FROM findings WHERE session_id = ? AND finding_id = ?", (session_id, finding_id)).fetchone()
            conn.close()
            return self._from_row(row) if row else None
        for (sid, _rule, _resource), finding in self._findings.items():
            if sid == session_id and finding["finding_id"] == finding_id:
                return deepcopy(finding)
        return None

    def update_status(self, session_id, finding_id, status):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            conn.execute("UPDATE findings SET status = ?, updated_at = ? WHERE session_id = ? AND finding_id = ?", (status, self._now(), session_id, finding_id))
            conn.commit()
            row = conn.execute("SELECT * FROM findings WHERE session_id = ? AND finding_id = ?", (session_id, finding_id)).fetchone()
            conn.close()
            return self._from_row(row) if row else None
        for key, finding in self._findings.items():
            if key[0] == session_id and finding["finding_id"] == finding_id:
                finding["status"] = status
                finding["updated_at"] = self._now()
                return deepcopy(finding)
        return None

    def resolve_matching(self, session_id, rule_id, resource_id):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            conn.execute("UPDATE findings SET status = 'RESOLVED', updated_at = ? WHERE session_id = ? AND rule_id = ? AND resource_id IS ?", (self._now(), session_id, rule_id, resource_id))
            conn.commit()
            row = conn.execute("SELECT * FROM findings WHERE session_id = ? AND rule_id = ? AND resource_id IS ?", (session_id, rule_id, resource_id)).fetchone()
            conn.close()
            return self._from_row(row) if row else None
        for key, finding in self._findings.items():
            if key == (session_id, rule_id, resource_id):
                finding["status"] = "RESOLVED"
                finding["updated_at"] = self._now()
                return deepcopy(finding)
        return None

    def clear_session(self, session_id):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            conn.execute("DELETE FROM findings WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
            return
        for key in list(self._findings):
            if key[0] == session_id:
                del self._findings[key]

    @staticmethod
    def _from_row(row):
        payload = dict(row)
        payload["evidence"] = json.loads(payload.get("evidence") or "[]")
        return payload