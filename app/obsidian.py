"""
Obsidian gear vault reader.

Reads gear item notes from the Obsidian vault (mounted read-only at OBSIDAN_MOUNT).
Gear notes are Markdown files with YAML frontmatter describing the item's properties.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import OBSIDAN_MOUNT
from app.models import GearItem


@dataclass
class ParseResult:
    items: list[GearItem]
    errors: list[str]
    source_path: str
    parsed_at: datetime


YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
YAML_FIELD_RE = re.compile(r"^(\w[\w-]*)\s*:\s*(.*)$")


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("\"'") for part in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "~"}:
        return None
    return value.strip("\"'")


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
    raw = match.group(1)
    result: dict[str, Any] = {}
    current_list_key: str | None = None

    for line in raw.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if current_list_key and line.startswith((" ", "\t")):
            item = line.strip()
            if item.startswith("-"):
                if result[current_list_key] is None:
                    result[current_list_key] = []
                result[current_list_key].append(_parse_scalar(item[1:].strip()))
                continue

        current_list_key = None
        field_match = YAML_FIELD_RE.match(line)
        if field_match:
            key, value = field_match.groups()
            parsed = _parse_scalar(value)
            result[key.strip()] = parsed
            if value.strip() == "":
                current_list_key = key.strip()
    return result if result else None


def _candidate_note_files(path: Path) -> list[Path]:
    gear_dirs = [
        path,
        path / "Gear",
        path / "Hiking" / "Gear",
        path / "Notes" / "Hiking" / "Gear",
    ]
    files: list[Path] = []
    for gear_dir in gear_dirs:
        if gear_dir.exists() and gear_dir.is_dir():
            files.extend(gear_dir.glob("*.md"))
    if files:
        return sorted(set(files))
    return sorted(path.rglob("*.md"))


def _looks_like_gear(frontmatter: dict[str, Any]) -> bool:
    gear_keys = {"type", "category", "role", "capabilities", "owned", "status", "field_observation"}
    return bool(gear_keys.intersection(frontmatter.keys()))


def read_gear_vault(source_path: str = OBSIDAN_MOUNT) -> ParseResult:
    """
    Scan the Obsidian vault for gear item notes and parse them.

    Notes are Markdown files with YAML frontmatter. The filename (without
    extension) becomes the item name; frontmatter provides type, category,
    role, capabilities, and notes.
    """
    path = Path(source_path)
    if not path.exists():
        return ParseResult(
            items=[], errors=[f"Obsidian vault not found: {source_path}"], source_path=source_path, parsed_at=datetime.now()
        )

    items: list[GearItem] = []
    errors: list[str] = []

    for md_file in _candidate_note_files(path):
        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"Failed to read {md_file.name}: {e}")
            continue

        frontmatter = parse_frontmatter(text)
        if frontmatter is None:
            continue
        if not _looks_like_gear(frontmatter):
            continue

        name = md_file.stem
        item = GearItem(
            id=None,
            name=_stringify(frontmatter.get("name")) or name,
            type=_stringify(frontmatter.get("type")),
            category=_stringify(frontmatter.get("category")),
            role=_stringify(frontmatter.get("role")),
            capabilities=_stringify(frontmatter.get("capabilities")),
            notes=_stringify(frontmatter.get("notes")),
            owner=_stringify(frontmatter.get("owner")) or "andy",
            parsed_at=datetime.now(),
            raw_yaml=frontmatter,
        )
        items.append(item)

    return ParseResult(
        items=items,
        errors=errors,
        source_path=str(path),
        parsed_at=datetime.now(),
    )
