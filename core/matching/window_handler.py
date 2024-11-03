import win32gui
import win32process
import psutil
from typing import Optional, Tuple

class WindowHandler:
    """Handles window detection and title parsing for specific applications"""
    
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

    @staticmethod
    def get_current_song() -> Optional[Tuple[str, str]]:
        """Get currently playing song info from Dopamine"""
        window_title = WindowHandler.get_dopamine_window()
        if window_title:
            try:
                artist, title = window_title.split(" - ", 1)
                return artist.strip(), title.strip()
            except ValueError:
                pass
        return None
