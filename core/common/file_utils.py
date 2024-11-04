# core/common/file_utils.py

"""
Common file operations shared between playlist_manager and song_matcher.
This module breaks circular dependencies by centralizing shared functionality.
"""

from pathlib import Path
from typing import Optional, Tuple, List, Set
import re
import os

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

def parse_artist_title(text: str) -> Optional[Tuple[str, str]]:
    """
    Parse artist and title from a string (window title or filename).
    
    Args:
        text: String to parse
        
    Returns:
        Tuple of (artist, title) if successful, None if parsing fails
    """
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

def is_exact_match(filename: str, artist: str, title: str) -> bool:
    """
    Check if a filename matches the artist and title exactly.
    
    Args:
        filename: The filename to check
        artist: Artist name to match
        title: Song title to match
        
    Returns:
        True if exact match, False otherwise
    """
    clean_filename = clean_string(filename)
    clean_artist = clean_string(artist)
    clean_title = clean_string(title)
    
    # Create pattern for exact artist-title match
    pattern = f"\\b{re.escape(clean_artist)}\\b.*\\b{re.escape(clean_title)}\\b"
    
    return bool(re.search(pattern, clean_filename))

def find_matches_in_playlist(playlist_path: Path, file_paths: Set[Path]) -> bool:
    """
    Check if any of the given file paths are present in the playlist.
    
    Args:
        playlist_path: Path to the playlist file
        file_paths: Set of file paths to check for
        
    Returns:
        True if any file is found in the playlist
    """
    try:
        with open(playlist_path, 'r', encoding='utf-8') as f:
            playlist_content = f.read()
            
        # Check each file
        for file_path in file_paths:
            # Try both forward and backward slashes
            file_str = str(file_path)
            file_str_alt = file_str.replace('\\', '/')
            if file_str in playlist_content or file_str_alt in playlist_content:
                return True
                
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
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

def search_music_directory(artist: str, title: str, music_dir: Path) -> List[Path]:
    """
    Search for matching files in the music directory.
    
    Args:
        artist: Artist name to match
        title: Song title to match
        music_dir: Base directory for music files
        
    Returns:
        List of matching file paths
    """
    matching_files = []
    
    for root, _, files in os.walk(music_dir):
        for file in files:
            if file.lower().endswith('.mp3'):
                file_path = Path(root) / file
                if is_exact_match(file_path.name, artist, title):
                    matching_files.append(file_path)
                    
    return matching_files