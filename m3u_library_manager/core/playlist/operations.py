from typing import List, Tuple, Optional
from pathlib import Path
import os

def find_missing_files(playlist_paths: List[str]) -> List[Tuple[int, str]]:
    """
    Find missing files in playlist.
    Returns list of (line_number, path) tuples.
    """
    missing = []
    for i, path in enumerate(playlist_paths, 1):
        if not os.path.exists(path):
            missing.append((i, path))
    return missing

def validate_playlist(file_path: str, paths: List[str]) -> List[str]:
    """
    Validate playlist entries and print issues.
    Returns list of error messages.
    """
    errors = []
    base_dir = os.path.dirname(os.path.abspath(file_path))
    
    for i, path in enumerate(paths, 1):
        # Check if path exists
        if not os.path.exists(path):
            errors.append(f"Line {i}: File not found: {path}")
            continue
            
        # Check if it's an MP3
        if not path.lower().endswith('.mp3'):
            errors.append(f"Line {i}: Not an MP3 file: {path}")
            
        # Check absolute/relative path
        if not os.path.isabs(path):
            abs_path = os.path.join(base_dir, path)
            if not os.path.exists(abs_path):
                errors.append(f"Line {i}: Invalid relative path: {path}")
    
    return errors

def clean_playlist(paths: List[str]) -> List[str]:
    """
    Clean playlist by removing duplicates and empty lines.
    Preserves order of first occurrence.
    """
    seen = set()
    cleaned = []
    
    for path in paths:
        path = path.strip()
        if path and path not in seen:
            cleaned.append(path)
            seen.add(path)
    
    return cleaned