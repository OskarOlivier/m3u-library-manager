# utils/id3/reader.py
from mutagen.easyid3 import EasyID3
from typing import Optional, Dict
import logging

def get_id3_tags(file_path: str) -> Optional[Dict[str, str]]:
    """
    Fetch all ID3 tags from an MP3 file.

    Args:
        file_path (str): Path to the MP3 file.
        
    Returns:
        Optional[Dict[str, str]]: Dictionary of tags if found, else None.
    """
    try:
        audio = EasyID3(file_path)
        return dict(audio)
    except Exception as e:
        logging.error(f"Failed to read ID3 tags from {file_path}: {e}")
        return None

def get_bpm_tag(file_path: str) -> Optional[float]:
    """
    Get the BPM tag from an MP3 file.

    Args:
        file_path (str): Path to the MP3 file.

    Returns:
        Optional[float]: BPM value if available, else None.
    """
    try:
        audio = EasyID3(file_path)
        bpm = audio.get('bpm', [None])[0]
        return float(bpm) if bpm else None
    except Exception as e:
        logging.error(f"Failed to read BPM tag from {file_path}: {e}")
        return None

