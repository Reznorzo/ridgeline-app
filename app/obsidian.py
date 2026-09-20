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
YAML_FIELD_RE = re.compile(r"^(\w[\w-]*)\s*:\s*(.+)$", re.MULTILINE)


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    """Extract YAML frontmatter from a Markdown note."""
    match = YAML_FRONTMATTER_RE.match(text)
    if not match:
        return None
    raw = match.group(1)
    result: dict[str, Any] = {}
    for line in raw.split("\n"):
        field_match = YAML_FIELD_RE.match(line)
        if field_match:
            key, value = field_match.groups()
            result[key.strip()] = value.strip()
    return result if result else None


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

    for md_file in sorted(path.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"Failed to read {md_file.name}: {e}")
            continue

        frontmatter = parse_frontmatter(text)
        if frontmatter is None:
            errors.append(f"No YAML frontmatter in {md_file.name}")
            continue

        name = md_file.stem
        item = GearItem(
            id=None,
            name=name,
            type=frontmatter.get("type", ""),
            category=frontmatter.get("category", ""),
            role=frontmatter.get("role", ""),
            capabilities=frontmatter.get("capabilities", ""),
            notes=frontmatter.get("notes", ""),
            owner=frontmatter.get("owner", "andy"),
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
