# gui/windows/pages/curation/handlers/playlist_handler.py

from PyQt6.QtCore import QObject
from pathlib import Path
import logging

from utils.m3u.parser import read_m3u

class PlaylistHandler(QObject):
    """Handles playlist operations"""
    
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.logger = logging.getLogger('playlist_handler')
        
    def toggle_song_in_playlist(self, playlist_path: Path):
        """Toggle current song in/out of playlist"""
        if not self.state.current_song:
            return
            
        try:
            # Get current highlight state
            is_highlighted = playlist_path in self.state.highlighted_playlists
            
            # Attempt to toggle
            success, new_count = self.state.playlist_manager.toggle_song_in_playlist(
                playlist_path,
                self.state.current_song.artist,
                self.state.current_song.title,
                not is_highlighted
            )
            
            if success:
                # Update state
                self.state.set_playlist_highlighted(playlist_path, not is_highlighted)
                self.state.update_playlist(playlist_path, new_count)
                
                # Calculate and update stats
                self._update_stats()
                
                # Show success message
                operation = "removed from" if is_highlighted else "added to"
                self.state.set_status(f"Successfully {operation} {playlist_path.name}")
            else:
                self.state.report_error(f"Failed to modify {playlist_path.name}")
                
        except Exception as e:
            self.logger.error(f"Error toggling song: {e}")
            self.state.report_error(f"Failed to modify playlist: {str(e)}")
            
    def _update_stats(self):
        """Update playlist statistics"""
        try:
            # Get all unique tracks from regular playlists
            playlisted_tracks = set()
            loved_tracks = set()
            
            for playlist in self.state.playlists_dir.glob("*.m3u"):
                try:
                    if playlist.name == "Love.bak.m3u":
                        loved_tracks.update(read_m3u(str(playlist)))
                    elif not playlist.name.startswith("Unplaylisted_"):
                        playlisted_tracks.update(read_m3u(str(playlist)))
                except Exception as e:
                    self.logger.error(f"Error reading {playlist.name}: {e}")
                    continue
                    
            # Calculate unplaylisted
            unplaylisted = loved_tracks - playlisted_tracks
            
            # Update state
            self.state.update_stats(len(playlisted_tracks), len(unplaylisted))
            
        except Exception as e:
            self.logger.error(f"Error updating stats: {e}")
            
    def cleanup(self):
        """Clean up resources"""
        pass