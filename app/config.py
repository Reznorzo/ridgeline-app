"""
Application configuration.
"""

import os
from pathlib import Path

# Default values — overridable via environment
OBSIDAN_MOUNT = os.environ.get("OBSIDAN_MOUNT", "/mnt/obsidian")
STATE_DIR = os.environ.get("STATE_DIR", "/var/lib/ridgeline")
DB_PATH = os.environ.get("DB_PATH", str(Path(STATE_DIR) / "ridgeline.db"))
PORT = int(os.environ.get("PORT", "8080"))
