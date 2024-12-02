# core/matching/window_handler.py
import win32gui
import win32process
import psutil
from dataclasses import dataclass
from typing import Optional, List, Tuple, NamedTuple
from pathlib import Path
import logging

@dataclass
class WindowTitleInfo:
    """Parsed information from window title."""
    artist: str
    title: str

class WindowHandler:
    """Handles window detection and title parsing for specific applications"""
    
    def __init__(self):
        self.logger = logging.getLogger('window_handler')
        self.last_title = None
        self.last_song_info: Optional[WindowTitleInfo] = None
        self._poll_interval = 1000  # Default 1 second
    
    def set_poll_interval(self, interval: int):
        """Set the polling interval in milliseconds."""
        self._poll_interval = interval
    
    @staticmethod
    def get_dopamine_window() -> Optional[str]:
        """Get the window title from Dopamine.exe process"""
        def enum_window_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    if process.name().lower() == "dopamine.exe":
                        title = win32gui.GetWindowText(hwnd)
                        if title and " - " in title:  # Basic validation
                            windows.append(title)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True

        windows = []
        win32gui.EnumWindows(enum_window_callback, windows)
        return windows[0] if windows else None

    def get_current_song(self) -> Optional[WindowTitleInfo]:
        """
        Get the current playing song info from window title.
        Does not include file matching - that's handled separately by SongMatcher.
        """
        window_title = self.get_dopamine_window()
        
        # Return cached info if window title hasn't changed
        if window_title == self.last_title and self.last_song_info is not None:
            return self.last_song_info
            
        # Return None if no window found
        if not window_title:
            self.last_title = None
            self.last_song_info = None
            return None
            
        self.last_title = window_title
        self.logger.debug(f"Detected window title: {window_title}")
        
        try:
            artist, title = window_title.split(" - ", 1)
            artist = artist.strip()
            title = title.strip()
                        
            # Cache the new song info
            self.last_song_info = WindowTitleInfo(artist=artist, title=title)
            return self.last_song_info
            
        except ValueError:
            self.logger.error(f"Invalid window title format: {window_title}")
            self.last_song_info = None
            return None
        except Exception as e:
            self.logger.error(f"Error getting current song: {e}")
            self.last_song_info = None
            return None

    def cleanup(self):
        """Clean up any resources."""
        self.last_title = None
        self.last_song_info = None