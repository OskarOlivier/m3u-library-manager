# core/matching/song_matcher.py
from pathlib import Path
from typing import List, Optional, Tuple
import os
import re

class SongMatcher:
    """Class for matching songs between window titles and filesystem paths"""
    
    @staticmethod
    def clean_string(s: str) -> str:
        """
        Clean a string for comparison by removing special characters and normalizing case.
        
        Args:
            s: String to clean
            
        Returns:
            Cleaned string
        """
        s = s.lower()
        # Preserve the hyphen between artist and title
        s = s.replace(" - ", " TITLESEPERATOR ")
        
        replacements = {
            ',': '', '&': '', '+': '', '(': '', ')': '', '[': '', ']': '',
            "'": '', '"': '', '!': '', '?': '', ';': '', ':': '', '_': ' '
        }
        for old, new in replacements.items():
            s = s.replace(old, new)
            
        # Restore the hyphen
        s = s.replace(" TITLESEPERATOR ", " - ")
        
        # Remove multiple spaces
        s = ' '.join(s.split())
        return s.strip()

    @staticmethod
    def parse_window_title(window_title: str) -> Optional[Tuple[str, str]]:
        """
        Parse artist and title from Dopamine window title.
        
        Args:
            window_title: The window title string
            
        Returns:
            Tuple of (artist, title) if successful, None if parsing fails
        """
        try:
            if " - " in window_title:
                artist, title = window_title.split(" - ", 1)
                artist = artist.strip()
                title = title.strip()
                if artist and title:
                    return artist, title
        except ValueError:
            pass
        return None

    def _is_exact_match(self, filename: str, artist: str, title: str) -> bool:
        """
        Check if a filename matches the artist and title exactly.
        
        Args:
            filename: The filename to check
            artist: Artist name to match
            title: Song title to match
            
        Returns:
            True if exact match, False otherwise
        """
        clean_filename = self.clean_string(filename)
        clean_artist = self.clean_string(artist)
        clean_title = self.clean_string(title)
        
        # Create pattern for exact artist-title match
        # This looks for artist and title as complete words
        pattern = f"\\b{re.escape(clean_artist)}\\b.*\\b{re.escape(clean_title)}\\b"
        
        return bool(re.search(pattern, clean_filename))

    def find_matches(self, 
                    title: str, 
                    artist: str, 
                    music_dir: str,
                    playlists_dir: Optional[str] = None) -> Tuple[List[Path], List[str]]:
        """
        Find matching files and playlists for a song.
        
        Args:
            title: Song title
            artist: Artist name
            music_dir: Base directory for music files
            playlists_dir: Optional directory containing M3U playlists
            
        Returns:
            Tuple of (matching_files, matching_playlists)
        """
        if not title or not artist:
            return [], []

        # Find matching files
        matching_files = []
        base_path = Path(music_dir)
        
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith('.mp3'):
                    file_path = Path(root) / file
                    if self._is_exact_match(file_path.name, artist, title):
                        matching_files.append(file_path)

        # Find playlists containing matches if playlists directory is provided
        matching_playlists = []
        if playlists_dir and matching_files:
            playlists_path = Path(playlists_dir)
            if playlists_path.exists():
                for playlist in playlists_path.glob("*.m3u"):
                    try:
                        with open(playlist, 'r', encoding='utf-8') as f:
                            playlist_content = f.read()
                            # Check if any matching file is in the playlist
                            for file in matching_files:
                                # Try both forward and backward slashes
                                file_str = str(file)
                                file_str_alt = file_str.replace('\\', '/')
                                if file_str in playlist_content or file_str_alt in playlist_content:
                                    matching_playlists.append(playlist.name)
                                    break
                    except UnicodeDecodeError:
                        # Try with different encoding if UTF-8 fails
                        try:
                            with open(playlist, 'r', encoding='cp1252') as f:
                                playlist_content = f.read()
                                for file in matching_files:
                                    file_str = str(file)
                                    file_str_alt = file_str.replace('\\', '/')
                                    if file_str in playlist_content or file_str_alt in playlist_content:
                                        matching_playlists.append(playlist.name)
                                        break
                        except Exception:
                            continue

        return matching_files, matching_playlists

    def find_matches_from_window_title(self, 
                                     window_title: str, 
                                     music_dir: str,
                                     playlists_dir: Optional[str] = None) -> Tuple[List[Path], List[str]]:
        """
        Find matches using a window title directly.
        
        Args:
            window_title: Dopamine window title
            music_dir: Base directory for music files
            playlists_dir: Optional directory containing M3U playlists
            
        Returns:
            Tuple of (matching_files, matching_playlists)
        """
        parsed = self.parse_window_title(window_title)
        if parsed:
            artist, title = parsed
            return self.find_matches(title, artist, music_dir, playlists_dir)
        return [], []
