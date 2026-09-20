"""
Gear item model for Obsidian-sourced gear data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class GearItem:
    id: int | None = None
    name: str = ""
    type: str = ""
    category: str = ""
    role: str = ""
    capabilities: str = ""
    notes: str = ""
    owner: str = "andy"
    parsed_at: datetime | None = None
    raw_yaml: dict[str, Any] | None = None

    @property
    def capability_list(self) -> list[str]:
        if not self.capabilities:
            return []
        return [c.strip() for c in self.capabilities.split(",")]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "role": self.role,
            "capabilities": self.capabilities,
            "notes": self.notes,
            "owner": self.owner,
        }
