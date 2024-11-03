# tests/conftest.py
from pathlib import Path

PLAYLIST_DIR = Path(r"D:\Music\Dopamine\Playlists")

def get_playlist_dir():
    return PLAYLIST_DIR
