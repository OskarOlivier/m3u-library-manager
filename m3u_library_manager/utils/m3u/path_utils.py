import os
from pathlib import Path
from typing import Optional

def is_absolute_path(path: str) -> bool:
    """Check if path is absolute"""
    return os.path.isabs(path)

def make_absolute(path: str, base_dir: str) -> str:
    """Convert relative path to absolute using base directory"""
    if is_absolute_path(path):
        return path
    return os.path.abspath(os.path.join(base_dir, path))

def make_relative(path: str, base_dir: str) -> str:
    """Convert absolute path to relative using base directory"""
    try:
        return os.path.relpath(path, base_dir)
    except ValueError:
        # If paths are on different drives, keep absolute
        return path

def verify_library_path(path: str) -> Optional[str]:
    """
    Verify if path matches library format:
    %albumartist% - %album% (%year%)/%track% %artist% - %title%.mp3
    Returns error message if invalid, None if valid
    """
    try:
        parts = Path(path).parts
        if len(parts) < 2:  # Need at least artist-album folder and filename
            return "Path too short"
            
        folder = parts[-2]  # Artist-album folder
        filename = parts[-1]  # Track filename
        
        # Check folder format
        if not (' - ' in folder and '(' in folder and ')' in folder):
            return "Invalid folder format"
            
        # Check file format
        if not (filename.endswith('.mp3') and ' - ' in filename):
            return "Invalid file format"
            
        return None
    except Exception as e:
        return f"Path verification error: {e}"