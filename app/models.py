"""
Gear item model for Obsidian-sourced gear data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class GearItem:
    id: str | int | None = None
    name: str = ""
    type: str = ""
    category: str = ""
    role: str = ""
    capabilities: str = ""
    notes: str = ""
    owner: str = "andy"
    source_path: str = ""
    source_hash: str = ""
    brand: str = ""
    model: str = ""
    owned: bool | None = None
    status: list[str] | None = None
    weight_g: float | None = None
    waterproof: bool | None = None
    protection_evidence: str = ""
    water_resistance: str = ""
    wind_resistance: str = ""
    breathability: str = ""
    ventilation: str = ""
    insulation: str = ""
    drying_speed: str = ""
    durability: str = ""
    season: str = ""
    temperature_min: float | None = None
    temperature_max: float | None = None
    layer_role: str = ""
    worn_over_categories: list[str] | None = None
    activities: dict[str, bool | None] | None = None
    conditions: dict[str, bool | None] | None = None
    features: list[str] | None = None
    preferred_when: str = ""
    avoid_when: str = ""
    preference_notes: str = ""
    pairings: list[dict[str, Any]] | None = None
    field_observations: list[dict[str, Any]] | None = None
    diagnostics: list[str] | None = None
    parsed_at: datetime | None = None
    raw_yaml: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.status = self.status or []
        self.worn_over_categories = self.worn_over_categories or []
        self.activities = self.activities or {}
        self.conditions = self.conditions or {}
        self.features = self.features or []
        self.pairings = self.pairings or []
        self.field_observations = self.field_observations or []
        self.diagnostics = self.diagnostics or []

    @property
    def capability_list(self) -> list[str]:
        values = [c.strip() for c in self.capabilities.split(",") if c.strip()]
        return list(dict.fromkeys([*values, *self.features]))

    @property
    def is_owned(self) -> bool:
        return self.owned is True or (self.owned is None and "owned" in self.status)

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
            "source_path": self.source_path,
            "source_hash": self.source_hash,
            "brand": self.brand,
            "model": self.model,
            "owned": self.owned,
            "status": self.status,
            "weight_g": self.weight_g,
            "waterproof": self.waterproof,
            "protection_evidence": self.protection_evidence,
            "water_resistance": self.water_resistance,
            "wind_resistance": self.wind_resistance,
            "breathability": self.breathability,
            "ventilation": self.ventilation,
            "insulation": self.insulation,
            "drying_speed": self.drying_speed,
            "durability": self.durability,
            "season": self.season,
            "temperature_min": self.temperature_min,
            "temperature_max": self.temperature_max,
            "layer_role": self.layer_role,
            "worn_over_categories": self.worn_over_categories,
            "activities": self.activities,
            "conditions": self.conditions,
            "features": self.features,
            "preferred_when": self.preferred_when,
            "avoid_when": self.avoid_when,
            "preference_notes": self.preference_notes,
            "pairings": self.pairings,
            "diagnostics": self.diagnostics,
        }
