from dataclasses import dataclass, field
from typing import Any


@dataclass
class Lab:
    id: int | None = None
    slug: str = ""
    title: str = ""
    description: str = ""
    category: str = "Cloud Security"
    difficulty: str = "Beginner"
    xp: int = 100
    status: str = "draft"
    metadata: str = "{}"
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "difficulty": self.difficulty,
            "xp": self.xp,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
