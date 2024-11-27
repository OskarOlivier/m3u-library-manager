# utils/m3u/parser.py

from pathlib import Path
from typing import List, Optional
import codecs
import os
from app.config import Config

class M3UParseError(Exception):
    """Custom exception for M3U parsing errors"""
    pass

def _normalize_path(path: str) -> str:
    """
    Normalize path to be relative to music library root.
    Strips E:\Albums prefix if present and converts to forward slashes.
    """
    # Convert Windows backslashes to forward slashes
    path = path.replace('\\', '/')
    
    # Remove music library root prefix if present
    library_prefix = str(Config.LOCAL_BASE).replace('\\', '/')
    if path.lower().startswith(library_prefix.lower()):
        path = path[len(library_prefix):].lstrip('/')
        
    return path

def _denormalize_path(relative_path: str) -> str:
    """
    Convert relative path back to absolute path with music library root.
    """
    # Ensure forward slashes
    relative_path = relative_path.replace('\\', '/')
    
    # Join with library root
    full_path = os.path.join(str(Config.LOCAL_BASE), relative_path)
    
    # Convert to Windows path format
    return full_path.replace('/', '\\')

def read_m3u(file_path: str) -> List[str]:
    """
    Read an M3U/M3U8 playlist file and return list of paths.
    All paths are normalized to be relative to music library root.
    
    Args:
        file_path: Path to the M3U file
        
    Returns:
        List of normalized paths
        
    Raises:
        M3UParseError if file cannot be read or parsed
    """
    try:
        with codecs.open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Fallback to system encoding if UTF-8 fails
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            raise M3UParseError(f"Failed to read playlist file: {e}")
    except Exception as e:
        raise M3UParseError(f"Failed to read playlist file: {e}")

    normalized_paths: List[str] = []
    for line_number, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Normalize path
        normalized_path = _normalize_path(line)
        
        # Verify path exists (using denormalized path for check)
        full_path = _denormalize_path(normalized_path)
        if not os.path.exists(full_path):
            print(f"Warning: File not found at line {line_number}: {full_path}")
            
        normalized_paths.append(normalized_path)

    return normalized_paths

def write_m3u(file_path: str, paths: List[str], use_absolute_paths: bool = True) -> None:
    """
    Write paths to M3U8 file.
    
    Args:
        file_path: Path to the M3U file to write
        paths: List of paths (relative or absolute)
        use_absolute_paths: Whether to write Windows-style absolute paths
                          (True for local, False for remote)
        
    Raises:
        M3UParseError if file cannot be written
    """
    try:
        with codecs.open(file_path, 'w', encoding='utf-8') as f:
            for path in paths:
                # Always normalize first
                normalized = _normalize_path(path)
                
                if use_absolute_paths:
                    # Convert to Windows absolute path for local files
                    final_path = _denormalize_path(normalized)
                else:
                    # Use normalized relative path for remote files
                    final_path = normalized
                    
                f.write(f"{final_path}\n")
    except Exception as e:
        raise M3UParseError(f"Failed to write playlist file: {e}")