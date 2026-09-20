"""
Obsidian gear vault reader.

Reads gear item notes from the Obsidian vault (mounted read-only at OBSIDIAN_MOUNT).
Gear notes are Markdown files with YAML frontmatter describing the item's properties.
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.config import OBSIDIAN_MOUNT
from app.models import GearItem


@dataclass
class ParseResult:
    items: list[GearItem]
    errors: list[str]
    source_path: str
    parsed_at: datetime


YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item is not None)
    return str(value)


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    """Extract YAML frontmatter from a Markdown note."""
    match = YAML_FRONTMATTER_RE.match(text)
    if not match:
        return None
    result = yaml.safe_load(match.group(1))
    return result if isinstance(result, dict) and result else None


KNOWN_GEAR_PATHS = (
    ("gear",),
    ("hiking", "gear"),
    ("notes", "hiking", "gear"),
    ("second brain", "notes", "hiking", "gear"),
)


def _candidate_note_files(path: Path) -> list[Path]:
    """Return Markdown notes that may be in a gear path or explicitly marked."""
    return sorted(path.rglob("*.md"))


def _is_known_gear_path(note: Path, vault: Path) -> bool:
    """Recognize the supported gear directories without accepting the vault root."""
    relative_parts = tuple(part.casefold() for part in note.relative_to(vault).parts[:-1])
    if vault.name.casefold() == "gear":
        return True
    return any(relative_parts[: len(prefix)] == prefix for prefix in KNOWN_GEAR_PATHS)


def _marker_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip().casefold().lstrip("#") for item in value]
    if value is None:
        return []
    return [part.strip().casefold().lstrip("#") for part in str(value).split(",")]


def _has_explicit_gear_marker(frontmatter: dict[str, Any]) -> bool:
    """Accept opt-in markers for gear notes stored outside known gear paths."""
    if frontmatter.get("gear") is True:
        return True

    for key in ("ridgeline", "kind", "note_type"):
        if "gear" in _marker_values(frontmatter.get(key)):
            return True

    return bool({"gear", "ridgeline/gear"}.intersection(_marker_values(frontmatter.get("tags"))))


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    if value is None:
        return []
    return [str(value).strip()] if str(value).strip() else []


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_mapping(value: Any) -> dict[str, bool | None]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item if isinstance(item, bool) else None for key, item in value.items()}


def _has_meaningful_value(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, dict):
        return any(_has_meaningful_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_meaningful_value(item) for item in value)
    return True


def _normalise_pairings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict) and _has_meaningful_value(item)]


def _diagnostics(frontmatter: dict[str, Any], name: str) -> list[str]:
    diagnostics: list[str] = []
    raw_status = frontmatter.get("status")
    status = {value.casefold() for value in _string_list(raw_status)}
    owned = frontmatter.get("owned")
    if owned is not None and not isinstance(owned, bool):
        diagnostics.append("owned must be true, false, or blank")
    elif isinstance(owned, bool) and raw_status is not None and (("owned" in status) != owned):
        diagnostics.append("owned and status disagree")

    for key in ("breathability", "ventilation", "insulation", "water_resistance", "wind_resistance"):
        value = frontmatter.get(key)
        if value is not None and str(value).casefold() not in {"none", "low", "moderate", "high"}:
            diagnostics.append(f"{key} has unrecognised rating: {value}")

    unknown_fields = [
        key
        for key in ("water_resistance", "wind_resistance", "breathability", "ventilation", "insulation")
        if frontmatter.get(key) is None
    ]
    if unknown_fields:
        diagnostics.append(f"Unknown fields: {', '.join(unknown_fields)}")
    if not frontmatter.get("category"):
        diagnostics.append(f"{name} has no category")
    return diagnostics


def _normalise_gear(frontmatter: dict[str, Any], note: Path, vault: Path, text: str) -> GearItem:
    relative_path = note.relative_to(vault).as_posix()
    relative_parts = note.relative_to(vault).parts
    gear_relative_parts = relative_parts
    if vault.name.casefold() != "gear":
        folded_parts = tuple(part.casefold() for part in relative_parts[:-1])
        for prefix in sorted(KNOWN_GEAR_PATHS, key=len, reverse=True):
            if folded_parts[: len(prefix)] == prefix:
                gear_relative_parts = relative_parts[len(prefix) :]
                break
    gear_relative_path = Path(*gear_relative_parts).as_posix()
    fallback_id = re.sub(r"[^a-z0-9]+", "-", gear_relative_path.removesuffix(".md").casefold()).strip("-")
    preferences = frontmatter.get("preferences") if isinstance(frontmatter.get("preferences"), dict) else {}
    evidence = (
        frontmatter.get("protection_evidence")
        if isinstance(frontmatter.get("protection_evidence"), dict)
        else {}
    )
    observations = frontmatter.get("field_observations")
    if not isinstance(observations, list):
        observations = []
    observations = [item for item in observations if isinstance(item, dict) and _has_meaningful_value(item)]

    name = _stringify(frontmatter.get("name")) or note.stem
    features = _string_list(frontmatter.get("features"))
    capabilities = _string_list(frontmatter.get("capabilities"))
    return GearItem(
        id=_stringify(frontmatter.get("id")) or f"gear:{fallback_id}",
        name=name,
        type=_stringify(frontmatter.get("type")),
        category=_stringify(frontmatter.get("category")),
        role=_stringify(frontmatter.get("role")) or _stringify(frontmatter.get("layer_role")),
        capabilities=", ".join(capabilities or features),
        notes=_stringify(frontmatter.get("notes")) or _stringify(preferences.get("notes")),
        owner=_stringify(frontmatter.get("owner")) or "andy",
        source_path=relative_path,
        source_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        brand=_stringify(frontmatter.get("brand")),
        model=_stringify(frontmatter.get("model")),
        owned=frontmatter.get("owned") if isinstance(frontmatter.get("owned"), bool) else None,
        status=_string_list(frontmatter.get("status")),
        weight_g=_number(frontmatter.get("weight_g")),
        waterproof=frontmatter.get("waterproof") if isinstance(frontmatter.get("waterproof"), bool) else None,
        protection_evidence=_stringify(evidence.get("sustained_rain")),
        water_resistance=_stringify(frontmatter.get("water_resistance")),
        wind_resistance=_stringify(frontmatter.get("wind_resistance")),
        breathability=_stringify(frontmatter.get("breathability")),
        ventilation=_stringify(frontmatter.get("ventilation")),
        insulation=_stringify(frontmatter.get("insulation")),
        drying_speed=_stringify(frontmatter.get("drying_speed")),
        durability=_stringify(frontmatter.get("durability")),
        season=_stringify(frontmatter.get("season")),
        temperature_min=_number(frontmatter.get("temperature_min")),
        temperature_max=_number(frontmatter.get("temperature_max")),
        layer_role=_stringify(frontmatter.get("layer_role")),
        worn_over_categories=_string_list(frontmatter.get("worn_over_categories")),
        activities=_bool_mapping(frontmatter.get("activity")),
        conditions=_bool_mapping(frontmatter.get("conditions")),
        features=features,
        preferred_when=_stringify(preferences.get("preferred_when")),
        avoid_when=_stringify(preferences.get("avoid_when")),
        preference_notes=_stringify(preferences.get("notes")),
        pairings=_normalise_pairings(frontmatter.get("pairings")),
        field_observations=observations,
        diagnostics=_diagnostics(frontmatter, name),
        parsed_at=datetime.now(UTC),
        raw_yaml=frontmatter,
    )


def read_gear_vault(source_path: str = OBSIDIAN_MOUNT) -> ParseResult:
    """
    Scan the Obsidian vault for gear item notes and parse them.

    Notes are Markdown files with YAML frontmatter. The filename (without
    extension) becomes the item name; frontmatter provides type, category,
    role, capabilities, and notes.
    """
    path = Path(source_path)
    if not path.exists():
        return ParseResult(
            items=[],
            errors=[f"Obsidian vault not found: {source_path}"],
            source_path=source_path,
            parsed_at=datetime.now(UTC),
        )

    items: list[GearItem] = []
    errors: list[str] = []

    for md_file in _candidate_note_files(path):
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as e:
            errors.append(f"Failed to read {md_file.name}: {e}")
            continue

        try:
            frontmatter = parse_frontmatter(text)
        except yaml.YAMLError as error:
            if _is_known_gear_path(md_file, path):
                errors.append(f"Failed to parse {md_file.name}: {error.problem or str(error)}")
            continue
        if frontmatter is None:
            continue
        if not (_is_known_gear_path(md_file, path) or _has_explicit_gear_marker(frontmatter)):
            continue
        items.append(_normalise_gear(frontmatter, md_file, path, text))

    return ParseResult(
        items=items,
        errors=errors,
        source_path=str(path),
        parsed_at=datetime.now(UTC),
    )
