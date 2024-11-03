"""Application-wide constants."""
from pathlib import Path

# File paths
APP_DIR = Path(__file__).parent.parent
CACHE_DIR = Path.home() / ".m3u_library_manager" / "cache"
LOG_DIR = Path.home() / ".m3u_library_manager" / "logs"

# UI Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
