# utils/playlist/stats.py
from pathlib import Path
from typing import Tuple, List, Set, Optional, Callable
from utils.m3u.parser import read_m3u

def should_exclude_playlist(playlist_name: str) -> bool:
    """
    Check if a playlist should be excluded from display and statistics.
    
    Args:
        playlist_name: Name of the playlist file
        
    Returns:
        bool: True if playlist should be excluded
    """
    excluded = {
        'Love.bak.m3u',
        'Unplaylisted_'  # Will match all Unplaylisted_ prefixed files
    }
    return any(name in playlist_name for name in excluded)

def calculate_playlist_stats(playlists_dir: Path, 
                           progress_callback: Optional[Callable[[int], None]] = None) -> Tuple[int, int]:
    """
    Calculate playlist statistics, excluding unplaylisted and backup files.
    
    Args:
        playlists_dir: Directory containing playlist files
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple[int, int]: (total_tracks, unplaylisted_tracks)
    """
    # Get all playlists first
    playlists = list(playlists_dir.glob("*.m3u"))
    total_playlists = len(playlists)
    
    # Initialize sets
    playlisted_tracks: Set[str] = set()
    loved_tracks: Set[str] = set()
    
    # Process all playlists
    for i, playlist in enumerate(playlists):
        if progress_callback:
            progress = int((i / total_playlists) * 100)
            progress_callback(progress)
            
        if playlist.name == "Love.bak.m3u":
            loved_tracks.update(read_m3u(str(playlist)))
        elif not should_exclude_playlist(playlist.name):
            playlisted_tracks.update(read_m3u(str(playlist)))
    
    # Final progress update
    if progress_callback:
        progress_callback(100)
    
    # Calculate unplaylisted (loved but not in any regular playlist)
    unplaylisted = loved_tracks - playlisted_tracks
    
    return len(playlisted_tracks), len(unplaylisted)

def get_regular_playlists(playlists_dir: Path) -> List[Path]:
    """
    Get list of regular playlists, excluding unplaylisted and backup files.
    
    Args:
        playlists_dir: Directory containing playlist files
        
    Returns:
        List[Path]: List of regular playlist paths
    """
    return [p for p in sorted(playlists_dir.glob("*.m3u")) 
            if not should_exclude_playlist(p.name)]