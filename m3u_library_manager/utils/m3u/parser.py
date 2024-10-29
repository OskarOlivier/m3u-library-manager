from pathlib import Path
from typing import List, Optional
import codecs
import os

class M3UParseError(Exception):
    """Custom exception for M3U parsing errors"""
    pass

def read_m3u(file_path: str) -> List[str]:
    """
    Read an M3U/M3U8 playlist file and return list of paths.
    Raises M3UParseError if file cannot be read or parsed.
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

    paths: List[str] = []
    for line_number, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Ensure path exists
        if not os.path.exists(line):
            print(f"Warning: File not found at line {line_number}: {line}")
        paths.append(line)

    return paths

def write_m3u(file_path: str, paths: List[str]) -> None:
    """
    Write paths to M3U8 file.
    Raises M3UParseError if file cannot be written.
    """
    try:
        with codecs.open(file_path, 'w', encoding='utf-8') as f:
            for path in paths:
                f.write(f"{path}\n")
    except Exception as e:
        raise M3UParseError(f"Failed to write playlist file: {e}")

def convert_path_separators(path: str, to_windows: bool = True) -> str:
    """
    Convert path separators between Windows and Unix style.
    Only when explicitly called.
    """
    if to_windows:
        return path.replace('/', '\\')
    return path.replace('\\', '/')