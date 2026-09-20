"""
Recommendation engine.

Generates wear/pack/optional/leave-home recommendations based on route context,
weather forecast, and personal gear preferences.
"""

from dataclasses import dataclass
from typing import Any

from app.models import GearItem


@dataclass
class RecommendationItem:
    gear_item: GearItem
    bucket: str  # wear, pack, optional, leave_home
    reason: str = ""
    cue: str = ""


@dataclass
class Recommendation:
    items: list[RecommendationItem]
    confidence: str = "medium"
    summary: str = ""
    conditions: dict[str, Any] = None


def generate_recommendation(
    route: dict[str, Any],
    forecast: dict[str, Any],
    gear_items: list[GearItem],
    exposure: str = "mixed",
    effort: str = "moderate",
    runs_hot: bool = True,
) -> Recommendation:
    """
    Generate a loadout recommendation.

    This is a placeholder implementation — the real engine will be calibrated
    over time. For now it returns a sensible baseline based on the prototype's
    example logic.
    """
    items: list[RecommendationItem] = []

    # Very simplified logic for the initial version
    # In production this will be a calibrated rules engine

    temp_high = forecast.get("high_route_temp_max", 8)
    rain_prob = forecast.get("rain_prob", 0.3)
    wind = forecast.get("wind_speed_mph", 0)

    # Footwear: prefer grip (Topo) unless cold/wet
    for item in gear_items:
        if item.name == "Topo Mountain Racer 4":
            bucket = "wear"
            reason = "Preferred for superior grip; cold/wet conditions not strong enough to outweigh."
            cue = "Pair with Waterproof Socks for muddy/wet sections"
            items.append(RecommendationItem(item, bucket, reason, cue))
        elif item.name == "Scarpa Terra GTX":
            bucket = "leave_home"
            reason = "The Topo and waterproof-sock pairing preserves preferred grip without needing the heavier boot."
            items.append(RecommendationItem(item, bucket, reason))
        elif item.name == "Waterproof Socks":
            bucket = "pack"
            reason = "Keeps the preferred Topos viable if the route becomes wet or muddy."
            items.append(RecommendationItem(item, bucket, reason))

    # Trousers: seasonal selection
    for item in gear_items:
        if item.name == "Mountain Equipment Comici":
            items.append(RecommendationItem(item, "wear",
                "Your mid-season option. Temporary wet legs remain an acceptable low-risk trade-off."))
        elif item.name == "Patagonia Terrebonne":
            items.append(RecommendationItem(item, "leave_home",
                "The cooler, changeable forecast favours the Comici today."))
        elif item.name == "Mountain Equipment Ibex":
            items.append(RecommendationItem(item, "leave_home",
                "Conditions are not cold enough for the winter option."))
        elif item.name == "Keela Lightning Pro":
            bucket = "optional"
            reason = "Rain is not currently prolonged enough to require overtrousers."
            items.append(RecommendationItem(item, bucket, reason))

    # Jackets: breathable outer for cool start, pack confirmed rain shell
    for item in gear_items:
        if item.name == "Mountain Equipment Echo":
            items.append(RecommendationItem(item, "wear",
                "The warmer breathable option suits the cool start without moving straight to the Saxon.",
                "If you become warm on the climb, open or remove before changing layers."))
        elif item.name == "Mountain Equipment Borealis":
            items.append(RecommendationItem(item, "leave_home",
                "Echo is the lighter breathable option for these conditions."))
        elif item.name == "Keela Saxon":
            items.append(RecommendationItem(item, "pack",
                "Reliable backup for sustained or wind-driven rain. Showers alone do not justify wearing it from the start.",
                "Change only if rain persists, effective temperature drops, or the Echo stops being comfortable."))

    confidence = "medium"
    summary = "Start breathable. Carry protection."

    return Recommendation(
        items=items,
        confidence=confidence,
        summary=summary,
        conditions={
            "valley_temp": f"{forecast.get('valley_temp_min', 12)}–{forecast.get('valley_temp_max', 14)}°C",
            "high_route_temp": f"{forecast.get('high_route_temp_min', 6)}–{forecast.get('high_route_temp_max', 8)}°C",
            "rain": forecast.get("rain", "Showers"),
            "wind": f"{forecast.get('wind_speed_mph', 22)}–{forecast.get('wind_speed_mph', 28)} mph",
        },
    )
