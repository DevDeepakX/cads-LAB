from __future__ import annotations

import copy
import json
from collections import defaultdict
from datetime import datetime, timezone

from .database import get_db_connection


class CloudProvider:
    def set_event_processor(self, processor):
        self._event_processor = processor

    def create_resource(self, session_id, resource_type, resource_name, region="ap-south-1", configuration=None, status="ACTIVE"):
        raise NotImplementedError

    def get_resource(self, session_id, resource_name):
        raise NotImplementedError

    def list_resources(self, session_id, resource_type=None):
        raise NotImplementedError

    def update_resource(self, session_id, resource_name, updates):
        raise NotImplementedError

    def delete_resource(self, session_id, resource_name):
        raise NotImplementedError

    def create_event(self, session_id, service, event_name, actor="student", resource_type="UNKNOWN", outcome="SUCCESS", severity="LOW", resource_name=None, metadata=None):
        raise NotImplementedError

    def list_events(self, session_id):
        raise NotImplementedError

    def reset_environment(self, session_id):
        raise NotImplementedError


class SimulatorProvider(CloudProvider):
    def __init__(self, db_url=None):
        self._resources = defaultdict(dict)
        self._events = defaultdict(list)
        self._event_processor = None
        self.db_url = db_url

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def session_exists(self, session_id):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            row = conn.execute("SELECT 1 FROM lab_sessions WHERE session_id = ?", (session_id,)).fetchone()
            conn.close()
            return row is not None
        return session_id in self._resources or session_id in self._events

    def create_resource(self, session_id, resource_type, resource_name, region="ap-south-1", configuration=None, status="ACTIVE"):
        if self.db_url:
            now = self._now()
            config = copy.deepcopy(configuration or {})
            conn = get_db_connection(self.db_url)
            conn.execute(
                "INSERT OR REPLACE INTO cloud_resources (session_id, resource_type, resource_name, region, configuration, state, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM cloud_resources WHERE session_id = ? AND resource_name = ?), ?), ?)",
                (session_id, resource_type, resource_name, region, json.dumps(config), json.dumps(config), status, session_id, resource_name, now, now),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM cloud_resources WHERE session_id = ? AND resource_name = ?", (session_id, resource_name)).fetchone()
            conn.close()
            return self._resource_from_row(row)
        bucket = self._resources.setdefault(session_id, {})
        resource = {
            "id": len(bucket) + 1,
            "session_id": session_id,
            "resource_type": resource_type,
            "resource_name": resource_name,
            "region": region,
            "configuration": copy.deepcopy(configuration or {}),
            "state": copy.deepcopy(configuration or {}),
            "status": status,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        bucket[resource_name] = resource
        return resource

    def get_resource(self, session_id, resource_name):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            row = conn.execute("SELECT * FROM cloud_resources WHERE session_id = ? AND resource_name = ?", (session_id, resource_name)).fetchone()
            conn.close()
            return self._resource_from_row(row) if row else None
        return copy.deepcopy(self._resources.get(session_id, {}).get(resource_name))

    def list_resources(self, session_id, resource_type=None):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            if resource_type:
                rows = conn.execute("SELECT * FROM cloud_resources WHERE session_id = ? AND resource_type = ? ORDER BY id", (session_id, resource_type)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM cloud_resources WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
            conn.close()
            return [self._resource_from_row(row) for row in rows]
        items = list(self._resources.get(session_id, {}).values())
        if resource_type:
            items = [item for item in items if item.get("resource_type") == resource_type]
        return copy.deepcopy(items)

    def update_resource(self, session_id, resource_name, updates):
        if self.db_url:
            resource = self.get_resource(session_id, resource_name)
            if not resource:
                raise KeyError(f"Resource {resource_name!r} not found in session {session_id!r}")
            config = resource.get("configuration", {})
            config.update(updates)
            conn = get_db_connection(self.db_url)
            conn.execute("UPDATE cloud_resources SET configuration = ?, state = ?, updated_at = ? WHERE session_id = ? AND resource_name = ?", (json.dumps(config), json.dumps(config), self._now(), session_id, resource_name))
            conn.commit()
            row = conn.execute("SELECT * FROM cloud_resources WHERE session_id = ? AND resource_name = ?", (session_id, resource_name)).fetchone()
            conn.close()
            return self._resource_from_row(row)
        resources = self._resources.setdefault(session_id, {})
        target = resources.get(resource_name)
        if not target:
            raise KeyError(f"Resource {resource_name!r} not found in session {session_id!r}")

        config = target.setdefault("configuration", {})
        if isinstance(config, str):
            config = json.loads(config)
        config.update(updates)
        target["configuration"] = config
        target["state"] = config
        target["updated_at"] = self._now()
        return copy.deepcopy(target)

    def delete_resource(self, session_id, resource_name):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            conn.execute("DELETE FROM cloud_resources WHERE session_id = ? AND resource_name = ?", (session_id, resource_name))
            conn.commit()
            conn.close()
            return True
        resources = self._resources.get(session_id, {})
        return resources.pop(resource_name, None)

    def remediate_s3_bucket(self, session_id, bucket_name, actor="student"):
        updates = {"public_access": False, "encryption": True, "logging": True}
        if not self.db_url:
            self.update_resource(session_id, bucket_name, updates)
            return self.create_event(session_id, "S3", "PutPublicAccessBlock", actor=actor, resource_type="S3_BUCKET", outcome="SUCCESS", severity="LOW", resource_name=bucket_name, metadata={"bucket": bucket_name, **updates})
        conn = get_db_connection(self.db_url)
        try:
            row = conn.execute("SELECT * FROM cloud_resources WHERE session_id = ? AND resource_name = ?", (session_id, bucket_name)).fetchone()
            if not row:
                raise KeyError(f"Resource {bucket_name!r} not found in session {session_id!r}")
            config = json.loads(row["configuration"] or "{}")
            config.update(updates)
            now = self._now()
            conn.execute("UPDATE cloud_resources SET configuration = ?, state = ?, updated_at = ? WHERE session_id = ? AND resource_name = ?", (json.dumps(config), json.dumps(config), now, session_id, bucket_name))
            number = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM cloud_events WHERE session_id = ?", (session_id,)).fetchone()[0]
            event_id = f"evt-{session_id}-{number:04d}"
            metadata = {"bucket": bucket_name, **updates}
            conn.execute("INSERT INTO cloud_events (event_id, session_id, timestamp, service, event_name, actor, resource_id, resource_name, resource_type, source_ip, region, outcome, severity, metadata) VALUES (?, ?, ?, 'S3', 'PutPublicAccessBlock', ?, ?, ?, 'S3_BUCKET', '10.10.10.10', 'ap-south-1', 'SUCCESS', 'LOW', ?)", (event_id, session_id, now, actor, bucket_name, bucket_name, json.dumps(metadata)))
            event = self._event_from_row(conn.execute("SELECT * FROM cloud_events WHERE event_id = ?", (event_id,)).fetchone())
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        if self._event_processor:
            self._event_processor.process(event)
        return event

    def create_event(self, session_id, service, event_name, actor="student", resource_type="UNKNOWN", outcome="SUCCESS", severity="LOW", resource_name=None, metadata=None, source_ip="10.10.10.10", region="ap-south-1"):
        resource = self.get_resource(session_id, resource_name) if resource_name else None
        event_number = len(self._events.get(session_id, [])) + 1
        if self.db_url:
            conn = get_db_connection(self.db_url)
            event_number = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM cloud_events WHERE session_id = ?", (session_id,)).fetchone()[0]
            conn.close()
        event = {
            "id": event_number,
            "event_id": f"evt-{session_id}-{event_number:04d}",
            "session_id": session_id,
            "timestamp": self._now(),
            "service": service,
            "event_name": event_name,
            "actor": actor,
            "resource_type": resource_type,
            "resource_id": resource_name or (resource.get("id") if resource else None),
            "resource_name": resource_name,
            "source_ip": source_ip,
            "region": region,
            "outcome": outcome,
            "severity": severity,
            "metadata": copy.deepcopy(metadata or {}),
        }
        if self.db_url:
            conn = get_db_connection(self.db_url)
            conn.execute("INSERT INTO cloud_events (event_id, session_id, timestamp, service, event_name, actor, resource_id, resource_name, resource_type, source_ip, region, outcome, severity, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (event["event_id"], session_id, event["timestamp"], service, event_name, actor, event["resource_id"], resource_name, resource_type, source_ip, region, outcome, severity, json.dumps(event["metadata"])))
            conn.commit()
            row = conn.execute("SELECT * FROM cloud_events WHERE event_id = ?", (event["event_id"],)).fetchone()
            conn.close()
            event = self._event_from_row(row)
        else:
            self._events.setdefault(session_id, []).append(event)
        if self._event_processor:
            self._event_processor.process(event)
        return event

    def list_events(self, session_id):
        if self.db_url:
            conn = get_db_connection(self.db_url)
            rows = conn.execute("SELECT * FROM cloud_events WHERE session_id = ? ORDER BY timestamp, id", (session_id,)).fetchall()
            conn.close()
            return [self._event_from_row(row) for row in rows]
        return copy.deepcopy(self._events.get(session_id, []))

    def reset_environment(self, session_id):
        if self._event_processor:
            self._event_processor.reset_session(session_id)
        if self.db_url:
            conn = get_db_connection(self.db_url)
            conn.execute("DELETE FROM cloud_events WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM cloud_resources WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
        self._resources.pop(session_id, None)
        self._events.pop(session_id, None)
        return True

    @staticmethod
    def _resource_from_row(row):
        payload = dict(row)
        payload["configuration"] = json.loads(payload.get("configuration") or "{}")
        payload["state"] = json.loads(payload.get("state") or payload.get("configuration") or "{}")
        return payload

    @staticmethod
    def _event_from_row(row):
        payload = dict(row)
        payload["event_id"] = payload.get("event_id") or f"evt-{payload['session_id']}-{payload['id']:04d}"
        payload["metadata"] = json.loads(payload.get("metadata") or "{}")
        return payload
