from dataclasses import dataclass
from typing import Any


@dataclass
class Finding:
    id: int | None = None
    finding_id: str = ""
    session_id: str = ""
    rule_id: str = ""
    title: str = ""
    service: str = ""
    resource_id: str | int | None = None
    severity: str = "MEDIUM"
    status: str = "OPEN"
    source: str = ""
    description: str = ""
    first_seen: str | None = None
    last_seen: str | None = None
    evidence: list[dict[str, Any]] | None = None
    recommendation: str = ""
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "session_id": self.session_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "service": self.service,
            "resource_id": self.resource_id,
            "severity": self.severity,
            "status": self.status,
            "source": self.source,
            "description": self.description,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "evidence": self.evidence or [],
            "recommendation": self.recommendation,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
