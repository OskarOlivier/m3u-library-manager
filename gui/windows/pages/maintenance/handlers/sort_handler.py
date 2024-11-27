# gui/windows/pages/maintenance/handlers/sort_handler.py

from pathlib import Path
import logging
from typing import List, Optional, Callable
from mutagen.easyid3 import EasyID3
from gui.dialogs.safety_dialogs import SafetyDialogs
from mutagen.mp3 import MP3

class SortHandler:
    """Handles playlist sorting operations with multiple criteria."""
    
    SORT_METHODS = {
        'path_asc': ('File Path (A-Z)', True),
        'path_desc': ('File Path (Z-A)', False),
        'duration_asc': ('Duration (Shortest)', True),
        'duration_desc': ('Duration (Longest)', False),
        'bpm_asc': ('BPM (Slowest)', True),
        'bpm_desc': ('BPM (Fastest)', False)
    }
    
    def __init__(self, state):
        self.state = state
        self.logger = logging.getLogger('sort_handler')
        
    def sort_playlist(self, playlist_path: Path, method: str):
        """
        Sort playlist using specified method.
        
        Args:
            playlist_path: Path to playlist file
            method: Sort method key from SORT_METHODS
        """
        if method not in self.SORT_METHODS:
            self.state.report_error(f"Invalid sort method: {method}")
            return
            
        try:
            self.state.is_sorting = True
            self.state.sort_started.emit(method)
            
            # Read playlist
            paths = self._read_playlist(playlist_path)
            if not paths:
                return
                
            # Get sort function
            sort_func = self._get_sort_function(method)
            if not sort_func:
                return
                
            # Sort paths
            sorted_paths = sorted(paths, key=sort_func, 
                                reverse=not self.SORT_METHODS[method][1])
                                
            # Write back
            if self._write_playlist(playlist_path, sorted_paths):
                self.state.sort_completed.emit(True)
            
        except Exception as e:
            self.logger.error(f"Sort failed: {e}")
            self.state.report_error(f"Sort failed: {str(e)}")
            self.state.sort_completed.emit(False)
        finally:
            self.state.is_sorting = False
            
    def _get_sort_function(self, method: str) -> Optional[Callable]:
        """Get appropriate sort function for method."""
        if method.startswith('path'):
            return str
        elif method.startswith('duration'):
            return self._get_duration
        elif method.startswith('bpm'):
            return self._get_bpm
        return None
        
    def _get_duration(self, path: str) -> float:
        """Get audio duration in seconds."""
        try:
            audio = MP3(path)
            return audio.info.length
        except Exception as e:
            self.logger.error(f"Error reading duration: {e}")
            return 0.0
            
    def _get_bpm(self, path: str) -> float:
        """Get BPM from ID3 tag."""
        try:
            audio = EasyID3(path)
            bpm = audio.get('bpm', [None])[0]
            return float(bpm) if bpm else 0.0
        except Exception as e:
            self.logger.error(f"Error reading BPM: {e}")
            return 0.0
            
    def _read_playlist(self, path: Path) -> Optional[List[str]]:
        """Read playlist with error handling."""
        try:
            from utils.m3u.parser import read_m3u
            return read_m3u(str(path))
        except Exception as e:
            self.logger.error(f"Error reading playlist: {e}")
            self.state.report_error(f"Failed to read playlist: {str(e)}")
            return None
            
    def _write_playlist(self, path: Path, paths: List[str]) -> bool:
        """Write playlist with error handling."""
        try:
            from utils.m3u.parser import write_m3u
            write_m3u(str(path), paths)
            return True
        except Exception as e:
            self.logger.error(f"Error writing playlist: {e}")
            self.state.report_error(f"Failed to write playlist: {str(e)}")
            return False
            
    def cleanup(self):
        """Clean up resources."""
        pass