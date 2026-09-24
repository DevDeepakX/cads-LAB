from dataclasses import dataclass
from typing import Any


@dataclass
class CloudResource:
    id: int | None = None
    session_id: str = ""
    resource_type: str = "UNKNOWN"
    resource_name: str = ""
    region: str = "ap-south-1"
    configuration: str = "{}"
    status: str = "ACTIVE"
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "region": self.region,
            "configuration": self.configuration,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
