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


if __name__ == "__main__":
    unittest.main()
