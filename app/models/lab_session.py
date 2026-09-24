from dataclasses import dataclass
from typing import Any


@dataclass
class LabSession:
    id: int | None = None
    session_id: str = ""
    user_id: str = ""
    lab_id: int | None = None
    started_at: str | None = None
    completed_at: str | None = None
    status: str = "NOT_STARTED"
    score: int = 0
    hints_used: int = 0
    commands_executed: int = 0
    metadata: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "lab_id": self.lab_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "score": self.score,
            "hints_used": self.hints_used,
            "commands_executed": self.commands_executed,
            "metadata": self.metadata,
        }
