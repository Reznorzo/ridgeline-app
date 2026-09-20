import asyncio
import unittest

from app.main import STATIC_DIR, root
from app.routers.health import health


class WebUITest(unittest.TestCase):
    def test_root_serves_web_ui(self):
        response = asyncio.run(root())

        self.assertIn("<title>Ridgeline</title>", response)
        self.assertIn("/static/app.js", response)
        self.assertIn('id="screen-plan"', response)
        self.assertIn('id="screen-loadout"', response)
        self.assertIn('class="mobile-nav"', response)
        self.assertTrue((STATIC_DIR / "styles.css").is_file())
        self.assertTrue((STATIC_DIR / "app.js").is_file())

    def test_ui_uses_local_field_tool_design_tokens(self):
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn("--bg: #0d120f", css)
        self.assertIn("--moss: #a8c982", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertNotIn("fonts.googleapis.com", css)

    def test_health_remains_json(self):
        response = asyncio.run(health())

        self.assertEqual(response.status, "ok")


if __name__ == "__main__":
    unittest.main()
