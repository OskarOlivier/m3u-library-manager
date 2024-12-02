# gui/windows/pages/curation/handlers/playlist_handler.py
from PyQt6.QtCore import QObject
from pathlib import Path
import logging

from utils.m3u.parser import read_m3u

class PlaylistHandler(QObject):
    """Handles playlist operations and ensures consistent selection state."""
    
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.logger = logging.getLogger('playlist_handler')
        
    def toggle_song_in_playlist(self, playlist_path: Path):
        """Toggle current song in/out of playlist with consistent selection state."""
        try:
            if not self.state.current_song or not self.state.current_file:
                self.logger.error("No current song or file")
                return

            # Get current selection state BEFORE any operations
            was_selected = playlist_path in self.state.selected_playlists

            # Store current selection state
            original_selections = self.state.selected_playlists.copy()

            # Get current state from playlist operations
            contains_song = self.state.playlist_manager.operations.contains_song(
                playlist_path, 
                str(self.state.current_file)
            )

            # Perform toggle operation
            success, new_count = self.state.playlist_manager.toggle_song_in_playlist(
                playlist_path,
                str(self.state.current_file),
                include=not was_selected  # Add if not selected, remove if selected
            )
            
            if success:
                # Update playlist state first
                self.state.update_playlist(playlist_path, new_count)    
                
                # Update selection state explicitly
                if was_selected:
                    self.state.remove_playlist_selection(playlist_path)
                else:
                    self.state.add_playlist_selection(playlist_path)
                
                # Force UI update with new count
                self.state.playlist_counts[playlist_path] = new_count
                self.state.playlist_updated.emit(playlist_path, new_count)
                
                operation = "added to" if not was_selected else "removed from"
                self.state.set_status(f"Successfully {operation} {playlist_path.name}")

                # Update stats without affecting selections
                self._update_stats()

            else:
                # Restore original selections on failure
                self.state.selected_playlists = original_selections
                self.logger.error("Toggle operation failed")
                self.state.report_error(f"Failed to modify {playlist_path.name}")
                
        except Exception as e:
            self.logger.error(f"Error toggling song: {e}", exc_info=True)
            self.state.report_error(f"Failed to modify playlist: {str(e)}")

    def _update_stats(self):
        """Update playlist statistics without affecting selections."""
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
        """Clean up resources."""
        pass
