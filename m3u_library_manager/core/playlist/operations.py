from pathlib import Path
from typing import List, Tuple, Optional
from utils.m3u.parser import read_m3u, write_m3u

class PlaylistOperations:
    """Handles playlist file operations"""
    
    @staticmethod
    def add_song_to_playlist(playlist_path: Path, song_path: str) -> bool:
        """Add a song to playlist if not present"""
        try:
            current_paths = read_m3u(str(playlist_path))
            if song_path not in current_paths:
                current_paths.append(song_path)
                write_m3u(str(playlist_path), current_paths)
            return True
        except Exception as e:
            print(f"Error adding to playlist: {e}")
            return False

    @staticmethod
    def remove_song_from_playlist(playlist_path: Path, song_path: str) -> bool:
        """Remove a song from playlist if present"""
        try:
            current_paths = read_m3u(str(playlist_path))
            if song_path in current_paths:
                current_paths.remove(song_path)
                write_m3u(str(playlist_path), current_paths)
            return True
        except Exception as e:
            print(f"Error removing from playlist: {e}")
            return False

    @staticmethod
    def get_track_count(playlist_path: Path) -> Optional[int]:
        """Get number of tracks in playlist"""
        try:
            tracks = read_m3u(str(playlist_path))
            return len(tracks)
        except Exception:
            return None

    @staticmethod
    def contains_song(playlist_path: Path, song_path: str) -> bool:
        """Check if playlist contains specific song"""
        try:
            current_paths = read_m3u(str(playlist_path))
            return song_path in current_paths
        except Exception:
            return False
