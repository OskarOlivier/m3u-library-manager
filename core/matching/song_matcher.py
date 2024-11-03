# core/matching/song_matcher.py

from pathlib import Path
from typing import List, Optional, Tuple
import os

from core.common.file_utils import (
    clean_string,
    parse_artist_title,
    is_exact_match,
    find_matches_in_playlist,
    search_music_directory
)

class SongMatcher:
    """Class for matching songs between window titles and filesystem paths"""
    
    @staticmethod
    def clean_string(s: str) -> str:
        """Wrapper for common clean_string function"""
        return clean_string(s)

    @staticmethod
    def parse_window_title(window_title: str) -> Optional[Tuple[str, str]]:
        """Parse artist and title from Dopamine window title"""
        return parse_artist_title(window_title)

    def find_matches(self, 
                    title: str, 
                    artist: str, 
                    music_dir: str,
                    playlists_dir: Optional[str] = None) -> Tuple[List[Path], List[str]]:
        """
        Find matching files and playlists for a song.
        """
        if not title or not artist:
            return [], []

        # Find matching files
        matching_files = search_music_directory(
            artist=artist,
            title=title,
            music_dir=Path(music_dir)
        )

        # Find playlists containing matches if playlists directory is provided
        matching_playlists = []
        if playlists_dir and matching_files:
            playlists_path = Path(playlists_dir)
            if playlists_path.exists():
                matching_files_set = set(matching_files)
                for playlist in playlists_path.glob("*.m3u"):
                    if find_matches_in_playlist(playlist, matching_files_set):
                        matching_playlists.append(playlist.name)

        return matching_files, matching_playlists

    def find_matches_from_window_title(self, 
                                     window_title: str, 
                                     music_dir: str,
                                     playlists_dir: Optional[str] = None) -> Tuple[List[Path], List[str]]:
        """Find matches using a window title directly"""
        parsed = self.parse_window_title(window_title)
        if parsed:
            artist, title = parsed
            return self.find_matches(title, artist, music_dir, playlists_dir)
        return [], []