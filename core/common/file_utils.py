# core/common/file_utils.py

from pathlib import Path 
from typing import Optional, Tuple, List, Set
import logging

logger = logging.getLogger('file_utils')

def parse_artist_title(text: str) -> Optional[Tuple[str, str]]:
    """Parse artist and title from window title string."""
    try:
        if " - " in text:
            artist, title = text.split(" - ", 1)
            artist = artist.strip()
            title = title.strip()
            if artist and title:
                return artist, title
    except ValueError:
        pass
    return None

def find_matches_in_playlist(playlist_path: Path, file_paths: Set[Path]) -> bool:
    """Check if any file paths exist in playlist."""
    try:
        with open(playlist_path, 'r', encoding='utf-8') as f:
            playlist_content = f.read()
            
        for file_path in file_paths:
            file_str = str(file_path)
            file_str_alt = file_str.replace('\\', '/')
            if file_str in playlist_content or file_str_alt in playlist_content:
                return True
                
    except UnicodeDecodeError:
        try:
            with open(playlist_path, 'r', encoding='cp1252') as f:
                playlist_content = f.read()
                for file_path in file_paths:
                    file_str = str(file_path)
                    file_str_alt = file_str.replace('\\', '/')
                    if file_str in playlist_content or file_str_alt in playlist_content:
                        return True
        except Exception:
            pass
            
    return False