"""
Pydantic schemas for API request/response validation.
"""

from typing import Any

from pydantic import BaseModel, Field


class RouteCreate(BaseModel):
    name: str
    distance_km: float | None = None
    ascent_m: float | None = None
    high_point_m: float | None = None
    expected_duration_min: float | None = None
    exposure: str = "mixed"


class RouteOut(BaseModel):
    id: int
    name: str
    distance_km: float | None = None
    ascent_m: float | None = None
    high_point_m: float | None = None
    expected_duration_min: float | None = None
    exposure: str | None = None
    gpx_hash: str | None = None
    gpx_revision: int = 1
    last_walked: str | None = None
    created_at: str


class GearItemOut(BaseModel):
    id: str | int | None = None
    name: str
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
    status: list[str] = Field(default_factory=list)
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
    worn_over_categories: list[str] = Field(default_factory=list)
    activities: dict[str, bool | None] = Field(default_factory=dict)
    conditions: dict[str, bool | None] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
    preferred_when: str = ""
    avoid_when: str = ""
    preference_notes: str = ""
    pairings: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)


class RecommendationItemOut(BaseModel):
    gear_item: GearItemOut
    bucket: str
    reason: str = ""
    cue: str = ""
    decisive_factors: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    depends_on_gear_ids: list[str] = Field(default_factory=list)
    combination_reason: str = ""


class RecommendationOut(BaseModel):
    items: list[RecommendationItemOut]
    confidence: str
    summary: str
    conditions: dict[str, Any] | None = None
    policy_version: str = ""
    warnings: list[str] = Field(default_factory=list)


class ForecastSnapshotOut(BaseModel):
    id: int | None = None
    route_id: int
    fetched_at: str
    valley_temp_min: float | None = None
    valley_temp_max: float | None = None
    high_route_temp_min: float | None = None
    high_route_temp_max: float | None = None
    rain_prob: float | None = None
    rain_amount_mm: float | None = None
    wind_speed_mph: float | None = None


class GPXImportOut(BaseModel):
    id: int
    name: str
    gpx_hash: str
    distance_km: float | None = None
    ascent_m: float | None = None
    high_point_m: float | None = None


class HealthOut(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
