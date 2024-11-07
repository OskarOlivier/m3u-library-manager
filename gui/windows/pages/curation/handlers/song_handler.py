# gui/windows/pages/curation/handlers/song_handler.py

from PyQt6.QtCore import QObject, QTimer
import logging
from typing import Optional, Tuple

from core.matching.window_handler import WindowHandler

class SongHandler(QObject):
    """Handles song detection and updates."""
    
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.logger = logging.getLogger('song_handler')
        
        # Create update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_current_song)
        
    def start(self):
        """Start song detection."""
        self.update_timer.start(1000)
        
    def stop(self):
        """Stop song detection."""
        self.update_timer.stop()
        
    def check_current_song(self):
        """Check for currently playing song."""
        try:
            song_info = WindowHandler.get_current_song()
            
            if song_info:
                artist, title = song_info
                if (not self.state.current_song or 
                    artist != self.state.current_song.artist or 
                    title != self.state.current_song.title):
                    # Song changed
                    self.state.set_current_song(artist, title)
                    self._update_playlist_highlights()
            elif self.state.current_song:
                # Song stopped
                self.state.clear_current_song()
                
        except Exception as e:
            self.logger.error(f"Error checking current song: {e}")
            
    def _update_playlist_highlights(self):
        """Update playlist highlights for current song."""
        if not self.state.current_song:
            return
            
        try:
            # Get playlists containing current song
            playlists = self.state.playlist_manager.get_song_playlists(
                self.state.current_song.artist,
                self.state.current_song.title
            )
            
            # Update highlights
            for playlist_path in self.state.playlist_counts.keys():
                self.state.set_playlist_highlighted(
                    playlist_path, 
                    playlist_path.name in playlists
                )
                
        except Exception as e:
            self.logger.error(f"Error updating highlights: {e}")
            
    def cleanup(self):
        """Clean up resources."""
        self.stop()