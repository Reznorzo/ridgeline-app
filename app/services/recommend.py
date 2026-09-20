"""Deterministic, versioned hiking loadout recommendation policy."""

from dataclasses import dataclass, field
from typing import Any

from app.models import GearItem


@dataclass(frozen=True)
class PolicyConfig:
    version: str = "2026-09-20.1"
    warm_temp_c: float = 10.0
    cold_temp_c: float = 4.0
    near_freezing_c: float = 1.0
    rain_trace_mm: float = 0.1
    rain_sustained_mm: float = 3.0
    rain_heavy_mm: float = 10.0
    rain_sustained_hours: float = 1.5
    rain_heavy_hours: float = 3.0
    long_route_minutes: float = 240.0
    wind_warning_mph: float = 35.0
    wind_severe_mph: float = 45.0


POLICY = PolicyConfig()


@dataclass
class RecommendationItem:
    gear_item: GearItem
    bucket: str
    reason: str
    cue: str = ""
    decisive_factors: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    depends_on_gear_ids: list[str] = field(default_factory=list)
    combination_reason: str = ""


@dataclass
class Recommendation:
    items: list[RecommendationItem]
    confidence: str
    summary: str
    conditions: dict[str, Any]
    policy_version: str = POLICY.version
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConditionEnvelope:
    temp_min_c: float | None
    temp_max_c: float | None
    rain_probability: float | None
    rain_amount_mm: float | None
    rain_duration_hours: float | None
    rain_at_start: bool | None
    wind_mph: float | None
    gust_mph: float | None
    duration_minutes: float | None
    exposure: str
    effort: str
    runs_hot: bool

    @property
    def forecast_available(self) -> bool:
        return any(
            value is not None
            for value in (
                self.temp_min_c,
                self.temp_max_c,
                self.rain_probability,
                self.rain_amount_mm,
                self.rain_duration_hours,
                self.wind_mph,
            )
        )

    @property
    def wetting_load(self) -> str:
        if self.rain_amount_mm is not None and self.rain_amount_mm >= POLICY.rain_heavy_mm:
            return "heavy"
        if self.rain_duration_hours is not None and self.rain_duration_hours >= POLICY.rain_heavy_hours:
            return "heavy"
        if self.rain_amount_mm is not None and self.rain_amount_mm >= POLICY.rain_sustained_mm:
            return "sustained"
        if self.rain_duration_hours is not None and self.rain_duration_hours >= POLICY.rain_sustained_hours:
            return "sustained"
        if self.rain_amount_mm is not None and self.rain_amount_mm >= POLICY.rain_trace_mm:
            return "intermittent"
        if self.rain_probability is not None and self.rain_probability >= 0.3:
            return "intermittent"
        if self.rain_amount_mm is not None or self.rain_probability is not None:
            return "dry"
        return "unknown"

    @property
    def thermal_consequence(self) -> str:
        if self.temp_min_c is None:
            return "unknown"
        if self.temp_min_c <= POLICY.cold_temp_c:
            return "high"
        if self.temp_min_c < POLICY.warm_temp_c:
            return "moderate"
        return "low"

    @property
    def is_long(self) -> bool:
        return self.duration_minutes is not None and self.duration_minutes >= POLICY.long_route_minutes

    @property
    def is_exposed(self) -> bool:
        return self.exposure == "exposed"


def _float_value(mapping: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = mapping.get(key)
        if value is None or isinstance(value, bool):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _build_envelope(
    route: dict[str, Any],
    forecast: dict[str, Any],
    exposure: str,
    effort: str,
    runs_hot: bool,
) -> ConditionEnvelope:
    temp_min = _float_value(forecast, "effective_temp_min", "high_route_temp_min", "valley_temp_min")
    temp_max = _float_value(forecast, "high_route_temp_max", "valley_temp_max")
    rain_probability = _float_value(forecast, "rain_prob", "precipitation_probability")
    if rain_probability is not None and rain_probability > 1:
        rain_probability /= 100
    return ConditionEnvelope(
        temp_min_c=temp_min,
        temp_max_c=temp_max,
        rain_probability=rain_probability,
        rain_amount_mm=_float_value(forecast, "rain_amount_mm", "precipitation_mm"),
        rain_duration_hours=_float_value(forecast, "rain_duration_hours", "wet_hours"),
        rain_at_start=forecast.get("rain_at_start") if isinstance(forecast.get("rain_at_start"), bool) else None,
        wind_mph=_float_value(forecast, "wind_speed_mph", "peak_wind_mph"),
        gust_mph=_float_value(forecast, "gust_speed_mph", "peak_gust_mph"),
        duration_minutes=_float_value(route, "expected_duration_min"),
        exposure=(exposure or "unknown").casefold(),
        effort=(effort or "moderate").casefold(),
        runs_hot=runs_hot,
    )


def _by_name(items: list[GearItem], name: str) -> GearItem | None:
    target = name.casefold()
    return next((item for item in items if item.name.casefold() == target), None)


def _confidence_min(*levels: str) -> str:
    rank = {"low": 0, "medium": 1, "high": 2}
    return min(levels, key=lambda level: rank[level])


def _condition_summary(envelope: ConditionEnvelope) -> dict[str, Any]:
    temperature = "Unknown"
    if envelope.temp_min_c is not None and envelope.temp_max_c is not None:
        temperature = f"{envelope.temp_min_c:g}–{envelope.temp_max_c:g}°C"
    elif envelope.temp_min_c is not None:
        temperature = f"Minimum {envelope.temp_min_c:g}°C"

    rain_probability = (
        f"{round(envelope.rain_probability * 100)}%" if envelope.rain_probability is not None else "Unknown"
    )
    return {
        "temperature": temperature,
        "thermal_consequence": envelope.thermal_consequence,
        "wetting_load": envelope.wetting_load,
        "rain_probability": rain_probability,
        "rain_amount_mm": envelope.rain_amount_mm,
        "wind_mph": envelope.wind_mph,
        "duration_minutes": envelope.duration_minutes,
        "exposure": envelope.exposure,
        "effort": envelope.effort,
    }


def generate_recommendation(
    route: dict[str, Any],
    forecast: dict[str, Any],
    gear_items: list[GearItem],
    exposure: str = "mixed",
    effort: str = "moderate",
    runs_hot: bool = True,
) -> Recommendation:
    """Return one explainable placement for every known owned gear item."""
    envelope = _build_envelope(route, forecast, exposure, effort, runs_hot)
    owned_items = [item for item in gear_items if item.is_owned]
    warnings: list[str] = []
    placements: dict[str, RecommendationItem] = {}

    def place(
        item: GearItem | None,
        bucket: str,
        reason: str,
        cue: str = "",
        factors: list[str] | None = None,
        caveats: list[str] | None = None,
        depends_on: list[GearItem | None] | None = None,
        combination_reason: str = "",
    ) -> None:
        if item is None:
            return
        placements[item.name] = RecommendationItem(
            gear_item=item,
            bucket=bucket,
            reason=reason,
            cue=cue,
            decisive_factors=factors or [],
            caveats=caveats or [],
            depends_on_gear_ids=[str(value.id) for value in (depends_on or []) if value is not None and value.id],
            combination_reason=combination_reason,
        )

    if not envelope.forecast_available:
        warnings.append("No forecast snapshot is available; weather-dependent placements are conservative and low confidence.")
    elif envelope.rain_amount_mm is None and envelope.rain_duration_hours is None:
        warnings.append("Rain amount and duration are missing; probability alone cannot establish protective-weather conditions.")

    peak_wind = max(value for value in (envelope.wind_mph, envelope.gust_mph) if value is not None) if any(
        value is not None for value in (envelope.wind_mph, envelope.gust_mph)
    ) else None
    if peak_wind is not None and peak_wind >= POLICY.wind_severe_mph:
        warnings.append("Severe wind is forecast; this loadout does not make an exposed route safe.")
    elif peak_wind is not None and peak_wind >= POLICY.wind_warning_mph and envelope.is_exposed:
        warnings.append("Strong wind on an exposed route raises the consequence of cold, rain, and poor footing.")
    if envelope.temp_min_c is not None and envelope.temp_min_c <= POLICY.near_freezing_c and envelope.is_exposed:
        warnings.append("Near-freezing exposed conditions require a separate safety and insulation review.")

    topo = _by_name(owned_items, "Topo Mountain Racer 4")
    scarpa = _by_name(owned_items, "Scarpa Terra GTX")
    waterproof_socks = _by_name(owned_items, "Waterproof Socks")
    cold_wet = envelope.thermal_consequence == "high" and envelope.wetting_load in {"intermittent", "sustained", "heavy"}
    wet_expected = envelope.wetting_load in {"intermittent", "sustained", "heavy"}

    if cold_wet and scarpa:
        place(
            scarpa,
            "wear",
            "Cold, wet conditions make known boot protection more important than the preferred Topo grip.",
            factors=[envelope.thermal_consequence, envelope.wetting_load],
        )
        place(topo, "leave_home", "Cold-wet protection outweighs the normal Topo grip preference for this plan.")
        place(waterproof_socks, "leave_home", "The selected waterproof boot already provides the planned foot protection.")
    elif topo:
        caveats = [] if wet_expected else ["Route-surface and grip evidence are not yet structured."]
        place(
            topo,
            "wear",
            "Preferred footwear because personal evidence favours its superior grip and the conditions do not require the warmer boot.",
            factors=["personal grip preference", envelope.thermal_consequence],
            caveats=caveats,
            depends_on=[waterproof_socks] if wet_expected else [],
            combination_reason="Waterproof Socks add wet-foot protection while retaining preferred Topo grip." if wet_expected else "",
        )
        place(scarpa, "leave_home", "Cold-wet protection is not strong enough to displace the preferred Topo footwear.")
        if waterproof_socks:
            if wet_expected:
                place(
                    waterproof_socks,
                    "pack",
                    "Rain or wet ground may require waterproof foot protection with the preferred Topos.",
                    "Put them on before prolonged wet ground or when feet are no longer staying acceptably dry.",
                    factors=[envelope.wetting_load],
                    depends_on=[topo],
                    combination_reason="Pairs with Topo Mountain Racer 4 for grip plus waterproof foot protection.",
                )
            elif envelope.wetting_load == "unknown":
                place(waterproof_socks, "optional", "Wet-ground conditions are unknown, so the Topo pairing has uncertain utility.")
            else:
                place(waterproof_socks, "leave_home", "Dry conditions do not require the waterproof-sock pairing.")
    else:
        warnings.append("No owned preferred trail footwear is available in the gear source.")
        if scarpa:
            place(scarpa, "wear", "This is the only known owned footwear option in the gear source.")

    terrebonne = _by_name(owned_items, "Patagonia Terrebonne Trousers")
    comici = _by_name(owned_items, "Mountain Equipment Comici Trousers")
    ibex = _by_name(owned_items, "Mountain Equipment Ibex Trousers")
    overtrousers = _by_name(owned_items, "Keela Lightning Pro Overtrousers") or _by_name(
        owned_items, "Keela Lightning Pro Trousers"
    )

    if envelope.temp_min_c is not None and envelope.temp_min_c <= POLICY.cold_temp_c and ibex:
        selected_trousers = ibex
        trouser_reason = "The cold condition band favours the known winter trouser option."
    elif envelope.temp_min_c is not None and envelope.temp_min_c >= POLICY.warm_temp_c and terrebonne:
        selected_trousers = terrebonne
        trouser_reason = "Warm moving conditions favour the most breathable normal-trouser option."
    elif comici:
        selected_trousers = comici
        trouser_reason = "Cool, changeable, or uncertain conditions favour the versatile mid-season trouser."
    else:
        selected_trousers = terrebonne or ibex
        trouser_reason = "Selected as the only known owned normal-trouser option."
        warnings.append("Normal-trouser coverage is incomplete in the gear source.")

    place(selected_trousers, "wear", trouser_reason, factors=[envelope.thermal_consequence, envelope.effort])
    for item in (terrebonne, comici, ibex):
        if item and item is not selected_trousers:
            place(item, "leave_home", f"{selected_trousers.name if selected_trousers else 'The selected trouser'} better matches today's thermal band.")

    consequential_route = envelope.is_long or envelope.is_exposed or envelope.thermal_consequence in {"moderate", "high"}
    if overtrousers:
        if envelope.wetting_load in {"sustained", "heavy"} and consequential_route:
            place(
                overtrousers,
                "pack",
                "Prolonged wetting and route consequence justify an overtrouser layer over the selected normal trousers.",
                "Add them when rain persists or wet legs begin to carry a thermal consequence.",
                factors=[envelope.wetting_load, envelope.thermal_consequence],
                depends_on=[selected_trousers],
                combination_reason="Adds longer-duration rain protection over the selected normal trousers.",
            )
        elif envelope.wetting_load == "intermittent":
            place(
                overtrousers,
                "optional" if not consequential_route else "pack",
                "Brief rain can be tolerated on the legs, but route consequence determines whether the overtrousers earn pack space.",
                factors=[envelope.wetting_load, envelope.exposure],
            )
        elif envelope.wetting_load == "unknown" and consequential_route:
            place(overtrousers, "optional", "Rain duration is unknown; this is a precaution rather than a predicted need.")
        else:
            place(overtrousers, "leave_home", "No prolonged cold-wet trigger justifies the overtrouser layer.")

    borealis = _by_name(owned_items, "Rab Borealis")
    echo = _by_name(owned_items, "Mountain Equipment Echo")
    saxon = _by_name(owned_items, "Keela Saxon")
    warm_moving = envelope.temp_min_c is not None and envelope.temp_min_c >= POLICY.warm_temp_c
    breathable_outer = borealis if warm_moving and borealis else echo or borealis
    other_outer = echo if breathable_outer is borealis else borealis

    if breathable_outer:
        outer_reason = (
            "The lighter breathable outer suits warm or high-output movement."
            if breathable_outer is borealis
            else "The warmer breathable outer suits cool, changeable, or uncertain moving conditions."
        )
        place(
            breathable_outer,
            "wear",
            outer_reason,
            "Vent or remove it if climbing effort makes it too warm; do not change to the shell for brief showers alone.",
            factors=[envelope.thermal_consequence, envelope.effort, "runs hot" if runs_hot else "neutral thermal profile"],
            caveats=["Sustained-rain protection still needs personal field evidence."]
            if breathable_outer.protection_evidence == "needs_test"
            else [],
        )
    if other_outer:
        place(other_outer, "leave_home", f"{breathable_outer.name if breathable_outer else 'The selected outer'} better matches the moving-temperature band.")

    if saxon:
        if envelope.wetting_load in {"sustained", "heavy"}:
            bucket = "wear" if envelope.rain_at_start is True and envelope.thermal_consequence == "high" else "pack"
            place(
                saxon,
                bucket,
                "It is the only current jacket with personally confirmed sustained-rain protection.",
                "Change when rain persists, becomes wind-driven, effective temperature drops, or the breathable layer stops being comfortable.",
                factors=[envelope.wetting_load, envelope.thermal_consequence, "confirmed protection"],
            )
        elif envelope.wetting_load == "intermittent":
            bucket = "pack" if consequential_route else "optional"
            place(
                saxon,
                bucket,
                "Intermittent showers do not justify wearing the shell from the start; route consequence determines whether to carry it.",
                "Use it only if rain persists or cold-wet consequence increases.",
                factors=[envelope.wetting_load, envelope.exposure],
            )
        elif envelope.wetting_load == "unknown":
            bucket = "pack" if consequential_route else "optional"
            place(saxon, bucket, "Missing rain amount and duration make the confirmed shell a cautious contingency, not a wear choice.")
        else:
            place(saxon, "leave_home", "Dry, low-consequence conditions do not trigger the confirmed rain shell.")
    elif envelope.wetting_load in {"sustained", "heavy"}:
        warnings.append("No owned jacket has confirmed sustained-rain protection.")

    if envelope.thermal_consequence == "high":
        known_insulation = [item for item in owned_items if item.insulation and item.insulation.casefold() != "none"]
        if not known_insulation:
            warnings.append("No owned item has known insulation for the cold condition band; review stop-layer coverage manually.")

    for item in owned_items:
        if item.name not in placements:
            place(
                item,
                "optional",
                "This owned item has no category-specific policy placement yet.",
                caveats=item.diagnostics,
            )

    gear_with_diagnostics = [item for item in owned_items if item.diagnostics]
    if gear_with_diagnostics:
        warnings.append(
            f"{len(gear_with_diagnostics)} gear item(s) contain unknown or inconsistent metadata; item diagnostics remain reviewable."
        )

    forecast_confidence = "low" if not envelope.forecast_available else "medium"
    if all(
        value is not None
        for value in (envelope.temp_min_c, envelope.temp_max_c, envelope.rain_amount_mm, envelope.wind_mph)
    ):
        forecast_confidence = "high"
    gear_confidence = "medium" if gear_with_diagnostics else "high"
    route_confidence = "high" if envelope.exposure in {"sheltered", "mixed", "exposed"} and envelope.duration_minutes else "medium"
    if envelope.exposure == "unknown":
        route_confidence = "low"
        warnings.append("Route exposure is unknown, reducing confidence in weather-consequence decisions.")
    confidence = _confidence_min(forecast_confidence, gear_confidence, route_confidence, "medium")

    if cold_wet:
        summary = "Prioritise cold-wet protection. Keep changes easy to reach."
    elif envelope.wetting_load in {"sustained", "heavy"}:
        summary = "Start comfortable. Keep proven rain protection immediately accessible."
    elif envelope.wetting_load == "dry" and envelope.thermal_consequence == "low":
        summary = "Keep it light and breathable."
    else:
        summary = "Start breathable. Carry protection when consequence justifies it."

    ordered_items = sorted(
        placements.values(),
        key=lambda item: ({"wear": 0, "pack": 1, "optional": 2, "leave_home": 3}[item.bucket], item.gear_item.name),
    )
    return Recommendation(
        items=ordered_items,
        confidence=confidence,
        summary=summary,
        conditions=_condition_summary(envelope),
        warnings=list(dict.fromkeys(warnings)),
    )
