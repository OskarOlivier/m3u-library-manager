# utils/id3/writer.py
from mutagen.easyid3 import EasyID3
import logging
from typing import Dict

def set_bpm_tag(file_path: str, bpm: float) -> bool:
    """
    Set the BPM tag in an MP3 file.

    Args:
        file_path (str): Path to the MP3 file.
        bpm (float): The BPM value to set.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        audio = EasyID3(file_path)
        audio['bpm'] = str(bpm)
        audio.save()
        return True
    except Exception as e:
        logging.error(f"Failed to set BPM tag for {file_path}: {e}")
        return False

def write_id3_tags(file_path: str, tags: Dict[str, str]) -> bool:
    """
    Write multiple ID3 tags to an MP3 file.

    Args:
        file_path (str): Path to the MP3 file.
        tags (Dict[str, str]): Dictionary of tag key-value pairs.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        audio = EasyID3(file_path)
        for tag, value in tags.items():
            audio[tag] = value
        audio.save()
        return True
    except Exception as e:
        logging.error(f"Failed to write tags to {file_path}: {e}")
        return False

