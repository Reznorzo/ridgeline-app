import tempfile
import unittest
from pathlib import Path

from app.obsidian import parse_frontmatter, read_gear_vault


class ObsidianParserTest(unittest.TestCase):
    def test_blank_values_remain_unknown_and_lists_normalize(self):
        frontmatter = parse_frontmatter(
            """---
type: shell
owned: true
field_observation:
capabilities:
  - rain
  - wind
---
Body
"""
        )

        self.assertEqual(frontmatter["type"], "shell")
        self.assertIs(frontmatter["field_observation"], None)
        self.assertEqual(frontmatter["capabilities"], ["rain", "wind"])
        self.assertTrue(frontmatter["owned"])

    def test_reads_hiking_gear_notes_from_vault_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            gear_dir = Path(temp_dir) / "Hiking" / "Gear"
            gear_dir.mkdir(parents=True)
            (gear_dir / "Topo Mountain Racer 4.md").write_text(
                """---
type: footwear
category: shoes
role: primary
capabilities: [grip, fast-drying]
field_observation:
---
""",
                encoding="utf-8",
            )
            (Path(temp_dir) / "Design.md").write_text(
                """---
topic: app-design
---
Not a gear note.
""",
                encoding="utf-8",
            )

            result = read_gear_vault(temp_dir)

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].name, "Topo Mountain Racer 4")
        self.assertEqual(result.items[0].capabilities, "grip, fast-drying")
        self.assertIs(result.items[0].raw_yaml["field_observation"], None)

    def test_excludes_non_gear_notes_with_generic_frontmatter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Project.md").write_text(
                """---
type: project
category: personal
status: active
---
This is not outdoor equipment.
""",
                encoding="utf-8",
            )
            journal = vault / "Journal"
            journal.mkdir()
            (journal / "Wet walk.md").write_text(
                """---
type: note
role: observation
capabilities: [reflection]
---
It rained.
""",
                encoding="utf-8",
            )

            result = read_gear_vault(temp_dir)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.items, [])

    def test_accepts_explicitly_marked_gear_outside_known_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            archive = vault / "Archive"
            archive.mkdir()
            (archive / "Rain mitts.md").write_text(
                """---
note_type: gear
type: gloves
category: clothing
---
""",
                encoding="utf-8",
            )
            (vault / "Poles.md").write_text(
                """---
gear: true
type: poles
---
""",
                encoding="utf-8",
            )

            result = read_gear_vault(temp_dir)

        self.assertEqual({item.name for item in result.items}, {"Rain mitts", "Poles"})

    def test_reads_nested_notes_from_a_gear_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nested = Path(temp_dir) / "Gear" / "Sleep"
            nested.mkdir(parents=True)
            (nested / "Quilt.md").write_text(
                """---
type: insulation
category: sleep
---
""",
                encoding="utf-8",
            )

            result = read_gear_vault(temp_dir)

        self.assertEqual([item.name for item in result.items], ["Quilt"])

    def test_reads_live_vault_gear_location_without_other_second_brain_notes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            gear_dir = vault / "Second Brain" / "Notes" / "Hiking" / "Gear"
            gear_dir.mkdir(parents=True)
            (gear_dir / "Trail shoes.md").write_text(
                """---
name: Trail shoes
category: Footwear
owned: true
---
""",
                encoding="utf-8",
            )
            concepts = vault / "Second Brain" / "concepts"
            concepts.mkdir(parents=True)
            (concepts / "Project.md").write_text(
                """---
type: concept
status: active
category: software
---
""",
                encoding="utf-8",
            )

            result = read_gear_vault(temp_dir)

        self.assertEqual([item.name for item in result.items], ["Trail shoes"])


if __name__ == "__main__":
    unittest.main()
