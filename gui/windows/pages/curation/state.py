# gui/windows/pages/curation/state.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set
from PyQt6.QtCore import QObject, pyqtSignal
import logging

from core.matching.song_matcher import SongMatchResult
from utils.m3u.parser import read_m3u, write_m3u

class CurationState(QObject):
    """Manages state and signals for curation page components."""
    
    # Song signals
    song_changed = pyqtSignal(object)  # Emits SongMatchResult
    song_cleared = pyqtSignal()
    
    # Playlist signals
    playlist_updated = pyqtSignal(Path, int)  # playlist_path, new_count
    playlist_selected = pyqtSignal(Path, bool)  # playlist_path, selected state
    playlist_selection_changed = pyqtSignal(set)  # Emits full set of selected playlists
    
    # Stats signals
    stats_updated = pyqtSignal(int, int)  # total_tracks, unplaylisted
    
    # Status signals
    status_changed = pyqtSignal(str)  # status message
    error_occurred = pyqtSignal(str)  # error message
    progress_updated = pyqtSignal(int)  # progress value
    file_selection_changed = pyqtSignal(Path)  # Selected filepath changed
    
    def __init__(self):
        super().__init__()
        self.current_song: Optional[SongMatchResult] = None
        self.current_file: Optional[Path] = None
        self.playlist_counts: Dict[Path, int] = {}
        self.selected_playlists: Set[Path] = set()
        self.playlist_manager = None
        self.playlists_dir = None
        self.logger = logging.getLogger('curation_state')
        
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
    def set_current_song(self, song_info: SongMatchResult):
        """Update current song with match information."""
        self.logger.debug(f"Setting current song: {song_info.artist} - {song_info.title}")
        self.current_song = song_info
        
        # Clear current selections before updating
        self._do_clear_selections()
        
        # Set initial file selection to best match if available
        if song_info.matches:
            best_match = song_info.matches[0][0]  # Best match
            self.set_current_file(best_match, from_song_change=True)
            
        self.song_changed.emit(song_info)

    def _do_clear_selections(self):
        """Internal method to clear selections with a single state update."""
        if self.selected_playlists:  # Only emit if there were selections
            old_selections = self.selected_playlists.copy()
            self.selected_playlists.clear()
            
            # Emit deselection signals for each playlist
            for playlist in old_selections:
                self.playlist_selected.emit(playlist, False)
            
            # Emit overall selection change
            self.playlist_selection_changed.emit(set())

    def clear_playlist_selections(self):
        """Public method to clear playlist selections."""
        self._do_clear_selections()

    def set_current_file(self, file_path: Path, from_song_change: bool = False):
        if self.current_file != file_path:
            self.current_file = file_path
            
            if not from_song_change:
                self.file_selection_changed.emit(file_path)
            
            if self.playlist_manager:
                self._do_clear_selections()  # Clear existing
                
                # Get playlists containing the file
                playlists = self.playlist_manager.get_song_playlists(str(file_path))
                
                # Update selections all at once
                new_selections = {Path(self.playlists_dir) / name for name in playlists}
                
                if new_selections:
                    self.selected_playlists = new_selections
                    
                    # Emit individual selection signals
                    for playlist in new_selections:
                        self.playlist_selected.emit(playlist, True)
                        
                    # Emit overall selection change
                    self.playlist_selection_changed.emit(new_selections)
            
    def clear_current_song(self):
        """Clear current song and file selection."""
        self.current_song = None
        self.current_file = None
        self.clear_playlist_selections()
        self.song_cleared.emit()
        
    def add_playlist_selection(self, playlist: Path, prevent_reset: bool = False) -> None:
        """
        Add a playlist to selected set.
        
        Args:
            playlist: Playlist to select
            prevent_reset: If True, don't emit signals (for batch updates)
        """
        if playlist not in self.selected_playlists:
            self.selected_playlists.add(playlist)
            if not prevent_reset:
                self.playlist_selected.emit(playlist, True)
                self.playlist_selection_changed.emit(self.selected_playlists)
        
    def remove_playlist_selection(self, playlist: Path, prevent_reset: bool = False) -> None:
        """
        Remove a playlist from selected set.
        
        Args:
            playlist: Playlist to deselect
            prevent_reset: If True, don't emit signals (for batch updates)
        """
        if playlist in self.selected_playlists:
            self.selected_playlists.discard(playlist)
            if not prevent_reset:
                self.playlist_selected.emit(playlist, False)
                self.playlist_selection_changed.emit(self.selected_playlists)

    def toggle_playlist_selection(self, playlist_path: Path) -> bool:
        """
        Toggle playlist selection state. Returns new state.
        Emits appropriate signals for UI updates.
        """
        self.logger.debug(f"Toggling playlist selection: {playlist_path}")
        was_selected = playlist_path in self.selected_playlists
        
        if was_selected:
            self.remove_playlist_selection(playlist_path)
            return False
        else:
            self.add_playlist_selection(playlist_path)
            return True
           
    def update_stats(self, total: int, unplaylisted: int):
        """Update playlist statistics."""
        self.stats_updated.emit(total, unplaylisted)
        
    def update_playlist(self, playlist: Path, count: int):
        """Update playlist track count."""
        self.logger.debug(f"Updating playlist {playlist.name} with count {count}")
        self.playlist_counts[playlist] = count
        self.playlist_updated.emit(playlist, count)
           
    def set_status(self, message: str):
        """Update status message."""
        self.status_changed.emit(message)
        
    def report_error(self, error: str):
        """Report an error condition."""
        self.logger.error(f"Error reported: {error}")
        self.error_occurred.emit(error)
        self.set_status(f"Error: {error}")
        
    def update_progress(self, value: int) -> None:
        """Update progress value."""
        self.progress_updated.emit(value)
        
    def collect_unplaylisted(self) -> bool:
        """Create playlist with unplaylisted loved tracks."""
        if not self.playlist_manager:
            return False
            
        try:
            self.logger.debug("Starting unplaylisted collection")
            playlisted_tracks = set()
            loved_tracks = set()
            
            # Get all playlisted tracks (excluding Unplaylisted_ playlists)
            for playlist in self.playlists_dir.glob("*.m3u"):
                if (not playlist.name.startswith("Unplaylisted_") and 
                    playlist.name != "Love.bak.m3u"):
                    paths = read_m3u(str(playlist))
                    playlisted_tracks.update(paths)
            
            # Get loved tracks
            loved_playlist = self.playlists_dir / "Love.bak.m3u"
            if not loved_playlist.exists():
                self.report_error("Love.bak.m3u not found")
                return False
                
            loved_tracks = set(read_m3u(str(loved_playlist)))
            
            # Calculate unplaylisted
            unplaylisted = sorted(loved_tracks - playlisted_tracks)
            
            if not unplaylisted:
                self.logger.info("No unplaylisted tracks found")
                return False
                
            # Create timestamp-based playlist name
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_playlist = self.playlists_dir / f"Unplaylisted_{timestamp}.m3u"
            
            # Write tracks with UTF-8 encoding
            write_m3u(str(new_playlist), unplaylisted)
            
            # Verify the written file
            try:
                written_tracks = read_m3u(str(new_playlist))
                self.logger.info(f"Successfully wrote {len(written_tracks)} tracks to {new_playlist.name}")
                if len(written_tracks) != len(unplaylisted):
                    raise ValueError("Written track count doesn't match expected")
            except Exception as e:
                self.report_error(f"Failed to verify written playlist: {str(e)}")
                return False
            
            # Try both common Dopamine install locations
            import subprocess
            dopamine_paths = [
                Path(r"C:\Program Files (x86)\Dopamine\Dopamine.exe")
            ]
            
            for dopamine_path in dopamine_paths:
                if dopamine_path.exists():
                    self.logger.info(f"Launching Dopamine from: {dopamine_path}")
                    subprocess.Popen([str(dopamine_path), str(new_playlist)])
                    return True
                    
            self.report_error("Dopamine.exe not found in expected locations")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to collect unplaylisted tracks: {e}", exc_info=True)
            self.report_error(f"Failed to collect unplaylisted: {str(e)}")
            return False
            
    def cache_current_state(self):
        """Cache current song and file selection state."""
        self.logger.debug("Caching current state")
        self.logger.debug(f"Current song: {self.current_song.artist + ' - ' + self.current_song.title if self.current_song else None}")
        self.logger.debug(f"Current file: {self.current_file}")
        # State is already maintained in self.current_song and self.current_file
        return bool(self.current_song and self.current_file)

    def restore_cached_state(self):
        """Restore cached song and file selection state."""
        if self.current_song and self.current_file:
            self.logger.debug("Restoring cached state")
            self.logger.debug(f"Restoring song: {self.current_song.artist} - {self.current_song.title}")
            self.logger.debug(f"Restoring file: {self.current_file}")
            self.song_changed.emit(self.current_song)
            self.file_selection_changed.emit(self.current_file)
            return True
        return False