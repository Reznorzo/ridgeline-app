import os
import subprocess
import sys
import unittest


class ConfigTest(unittest.TestCase):
    def test_correctly_spelled_obsidian_mount_environment_variable_wins(self):
        environment = os.environ.copy()
        environment["OBSIDIAN_MOUNT"] = "/test/correct"
        environment["OBSIDAN_MOUNT"] = "/test/legacy"

        result = subprocess.run(
            [sys.executable, "-c", "from app.config import OBSIDIAN_MOUNT; print(OBSIDIAN_MOUNT)"],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )

        self.assertEqual(result.stdout.strip(), "/test/correct")

    def test_legacy_misspelling_remains_supported(self):
        environment = os.environ.copy()
        environment.pop("OBSIDIAN_MOUNT", None)
        environment["OBSIDAN_MOUNT"] = "/test/legacy"

        result = subprocess.run(
            [sys.executable, "-c", "from app.config import OBSIDIAN_MOUNT; print(OBSIDIAN_MOUNT)"],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )

        self.assertEqual(result.stdout.strip(), "/test/legacy")


if __name__ == "__main__":
    unittest.main()
