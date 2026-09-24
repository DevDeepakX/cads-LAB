from dataclasses import dataclass
from typing import Any


@dataclass
class CloudEvent:
    id: int | None = None
    session_id: str = ""
    timestamp: str | None = None
    service: str = "UNKNOWN"
    event_name: str = "UNKNOWN"
    actor: str = "student"
    resource_id: int | None = None
    resource_type: str = "UNKNOWN"
    source_ip: str = ""
    region: str = "ap-south-1"
    outcome: str = "SUCCESS"
    severity: str = "MEDIUM"
    metadata: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "service": self.service,
            "event_name": self.event_name,
            "actor": self.actor,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "source_ip": self.source_ip,
            "region": self.region,
            "outcome": self.outcome,
            "severity": self.severity,
            "metadata": self.metadata,
        }
