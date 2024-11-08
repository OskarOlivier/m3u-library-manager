# utils/cache/cleanup.py
from pathlib import Path
from typing import Tuple

def get_unplaylisted_size(playlists_dir: Path) -> Tuple[int, int]:
    """
    Get the total size and count of Unplaylisted m3u files.
    
    Returns:
        Tuple[int, int]: (size_in_kb, file_count)
    """
    total_size = 0
    file_count = 0
    
    for playlist in playlists_dir.glob("Unplaylisted_*.m3u"):
        if playlist.exists():
            total_size += playlist.stat().st_size
            file_count += 1
            
    return (total_size // 1024), file_count  # Convert to KB

def cleanup_unplaylisted(playlists_dir: Path) -> Tuple[int, int]:
    """
    Remove all Unplaylisted m3u files.
    
    Returns:
        Tuple[int, int]: (size_cleaned_kb, files_removed)
    """
    size_kb, count = get_unplaylisted_size(playlists_dir)
    
    for playlist in playlists_dir.glob("Unplaylisted_*.m3u"):
        if playlist.exists():
            playlist.unlink()
            
    return size_kb, count