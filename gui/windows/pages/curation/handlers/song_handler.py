# gui/windows/pages/curation/handlers/song_handler.py

from PyQt6.QtCore import QObject, QTimer
from typing import Optional
import logging

from core.matching.window_handler import WindowHandler, WindowTitleInfo
from core.matching.song_matcher import SongMatcher, SongMatchResult
from app.config import Config

class SongHandler(QObject):
    
    def start(self):
        """Start monitoring for song changes."""
        if self.update_timer is None:
            self._create_timer()
        self._is_checking_first_time = True
        self.update_timer.start(1000)  # Check every second

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.logger = logging.getLogger('song_handler')
        self.window_handler = WindowHandler()
        self.song_matcher = SongMatcher()
        self.last_window_title_info: Optional[WindowTitleInfo] = None
        self.update_timer = None
        self._is_checking_first_time = False
        self._create_timer()

    def _create_timer(self):
        """Create the update timer with proper initialization."""
        if self.update_timer is not None:
            self.stop()
            
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_current_song)
        
    def start(self):
        """Start monitoring for song changes."""
        if self.update_timer is None:
            self._create_timer()
        self.update_timer.start(1000)  # Check every second
        
    def stop(self):
        """Stop monitoring for song changes."""
        if self.update_timer is not None:
            self.update_timer.stop()
            self.update_timer.deleteLater()
            self.update_timer = None

    def check_current_song(self):
        """Check for song changes in Dopamine window."""
        try:
            window_info = self.window_handler.get_current_song()
            
            # Clear state if no song is playing and there's no cached state
            if not window_info:
                if self.state.current_song and not self._is_checking_first_time:
                    self.logger.debug("Song playback stopped")
                    self.state.clear_current_song()
                    self.last_window_title_info = None
                return
                
            # Check if song has changed
            if (self.last_window_title_info is None or
                window_info.artist != self.last_window_title_info.artist or
                window_info.title != self.last_window_title_info.title):
                
                self.logger.debug(f"New song detected: {window_info.artist} - {window_info.title}")
                
                # Start matching phase
                self.state.set_status("Finding matching files...")
                
                # Find matching files with progress updates
                matches = self.song_matcher.find_matches(
                    window_info.artist,
                    window_info.title,
                    str(Config.LOCAL_BASE),
                    self.state.update_progress
                )
                
                # Create match result
                song_info = SongMatchResult(
                    artist=window_info.artist,
                    title=window_info.title,
                    matches=matches
                )
                
                # Update state
                self.state.set_current_song(song_info)
                self.last_window_title_info = window_info
                
                # Clear progress
                self.state.update_progress(0)
                
        except Exception as e:
            self.logger.error(f"Error checking current song: {e}")
        finally:
            self._is_checking_first_time = False

    def update_filepath_selection(self, file_path):
        """Handle manual filepath selection from UI."""
        self.logger.debug(f"Manual file selection: {file_path}")
        
        try:
            if not self.state.current_song or file_path != self.state.current_file:
                # Update state with new file selection
                self.state.set_current_file(file_path)
                
        except Exception as e:
            self.logger.error(f"Error updating filepath selection: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop()
            if hasattr(self, 'window_handler'):
                self.window_handler.cleanup()
        except Exception as e:
            self.logger.error(f"Error cleaning up song handler: {e}")