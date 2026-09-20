"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
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
    exposure: str
    gpx_hash: str | None = None
    gpx_revision: int = 1
    last_walked: str | None = None
    created_at: str


class GearItemOut(BaseModel):
    id: int | None = None
    name: str
    type: str = ""
    category: str = ""
    role: str = ""
    capabilities: str = ""
    notes: str = ""
    owner: str = "andy"


class RecommendationItemOut(BaseModel):
    gear_item: GearItemOut
    bucket: str
    reason: str = ""
    cue: str = ""


class RecommendationOut(BaseModel):
    items: list[RecommendationItemOut]
    confidence: str
    summary: str
    conditions: dict[str, Any] | None = None


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
