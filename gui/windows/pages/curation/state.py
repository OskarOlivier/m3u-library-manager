# gui/windows/pages/curation/state.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set
from PyQt6.QtCore import pyqtSignal
import logging
import json

from core.matching.song_matcher import SongMatchResult
from core.state.base_state import BaseState
from utils.m3u.parser import read_m3u, write_m3u

@dataclass
class CurationStateData:
    """Data class for serializable state."""
    current_song: Optional[dict] = None  # Serialized SongMatchResult
    current_file: Optional[str] = None
    selected_playlists: list[str] = None  # List of playlist paths
    playlist_counts: dict[str, int] = None  # Map of playlist paths to counts

class CurationState(BaseState[CurationStateData]):
    """Manages state and signals for curation page components."""
    
    # Song signals
    song_changed = pyqtSignal(object)  # Emits SongMatchResult
    song_cleared = pyqtSignal()
    file_selection_changed = pyqtSignal(Path)  # Selected filepath changed
    
    # Playlist signals
    playlist_updated = pyqtSignal(Path, int)  # playlist_path, new_count
    playlist_selected = pyqtSignal(Path, bool)  # playlist_path, selected state
    playlist_selection_changed = pyqtSignal(set)  # Emits full set of selected playlists
    
    # Stats signals
    stats_updated = pyqtSignal(int, int)  # total_tracks, unplaylisted
    
    def __init__(self):
        super().__init__()
        self.current_song: Optional[SongMatchResult] = None
        self.current_file: Optional[Path] = None
        self.playlist_counts: Dict[Path, int] = {}
        self.selected_playlists: Set[Path] = set()
        self.playlists_dir: Optional[Path] = None
        self.playlist_manager = None

    async def _do_initialize(self) -> None:
        """Initialize state data."""
        await super()._do_initialize()
        self.set_status("Curation state initialized")

    def _do_reset(self) -> None:
        """Reset state to initial values."""
        self.clear_current_song()
        self.clear_playlist_selections()
        self.playlist_counts.clear()

    def _get_serializable_state(self) -> dict:
        """Convert state to serializable format."""
        return {
            'current_song': self._serialize_song_result(self.current_song) if self.current_song else None,
            'current_file': str(self.current_file) if self.current_file else None,
            'selected_playlists': [str(p) for p in self.selected_playlists],
            'playlist_counts': {str(k): v for k, v in self.playlist_counts.items()}
        }

    def _restore_from_state(self, state_data: dict) -> None:
        """Restore state from serialized data."""
        if state_data.get('current_song'):
            self.current_song = self._deserialize_song_result(state_data['current_song'])
            
        if state_data.get('current_file'):
            self.current_file = Path(state_data['current_file'])
            
        self.selected_playlists = {Path(p) for p in state_data.get('selected_playlists', [])}
        self.playlist_counts = {Path(k): v for k, v in state_data.get('playlist_counts', {}).items()}
        
        # Re-emit signals for restored state
        if self.current_song:
            self.song_changed.emit(self.current_song)
        if self.selected_playlists:
            self.playlist_selection_changed.emit(self.selected_playlists)

    def _serialize_song_result(self, result: Optional[SongMatchResult]) -> Optional[dict]:
        """Serialize SongMatchResult to dictionary."""
        if not result:
            return None
        return {
            'artist': result.artist,
            'title': result.title,
            'matches': [(str(path), prob) for path, prob in result.matches]
        }

    def _deserialize_song_result(self, data: dict) -> SongMatchResult:
        """Create SongMatchResult from serialized data."""
        return SongMatchResult(
            artist=data['artist'],
            title=data['title'],
            matches=[(Path(path), prob) for path, prob in data['matches']]
        )

    def set_current_song(self, song_info: SongMatchResult):
        """Update current song with match information."""
        self.current_song = song_info
        self._clear_selections()
        
        if song_info.matches:
            best_match = song_info.matches[0][0]  # Best match
            self.set_current_file(best_match, from_song_change=True)
            
        self.song_changed.emit(song_info)

    def clear_current_song(self):
        """Clear current song and file selection."""
        self.current_song = None
        self.current_file = None
        self.clear_playlist_selections()
        self.song_cleared.emit()

    def set_current_file(self, file_path: Path, from_song_change: bool = False):
        """Update current file selection."""
        if self.current_file != file_path:
            self.current_file = file_path
            
            if not from_song_change:
                self.file_selection_changed.emit(file_path)
            
            if self.playlist_manager:
                self._clear_selections()  # Clear existing
                
                playlists = self.playlist_manager.get_song_playlists(str(file_path))
                new_selections = {Path(self.playlists_dir) / name for name in playlists}
                
                if new_selections:
                    self.selected_playlists = new_selections
                    for playlist in new_selections:
                        self.playlist_selected.emit(playlist, True)
                    self.playlist_selection_changed.emit(new_selections)

    def add_playlist_selection(self, playlist: Path):
        """Add playlist to selected set."""
        if playlist not in self.selected_playlists:
            self.selected_playlists.add(playlist)
            self.playlist_selected.emit(playlist, True)
            self.playlist_selection_changed.emit(self.selected_playlists)

    def remove_playlist_selection(self, playlist: Path):
        """Remove playlist from selected set."""
        if playlist in self.selected_playlists:
            self.selected_playlists.discard(playlist)
            self.playlist_selected.emit(playlist, False)
            self.playlist_selection_changed.emit(self.selected_playlists)

    def clear_playlist_selections(self):
        """Clear all playlist selections."""
        self._clear_selections()

    def _clear_selections(self):
        """Internal method to clear selections with a single state update."""
        if self.selected_playlists:
            old_selections = self.selected_playlists.copy()
            self.selected_playlists.clear()
            for playlist in old_selections:
                self.playlist_selected.emit(playlist, False)
            self.playlist_selection_changed.emit(set())

    def update_stats(self, total: int, unplaylisted: int):
        """Update playlist statistics."""
        self.stats_updated.emit(total, unplaylisted)

    def update_playlist(self, playlist: Path, count: int):
        """Update playlist track count."""
        self.playlist_counts[playlist] = count
        self.playlist_updated.emit(playlist, count)

    def collect_unplaylisted(self) -> bool:
        """Create playlist with unplaylisted loved tracks."""
        if not self.playlist_manager:
            return False

        try:
            playlisted_tracks = set()
            loved_tracks = set()
            
            for playlist in self.playlists_dir.glob("*.m3u"):
                if (not playlist.name.startswith("Unplaylisted_") and 
                    playlist.name != "Love.bak.m3u"):
                    paths = read_m3u(str(playlist))
                    playlisted_tracks.update(paths)
            
            loved_playlist = self.playlists_dir / "Love.bak.m3u"
            if not loved_playlist.exists():
                self.report_error("Love.bak.m3u not found")
                return False
                
            loved_tracks = set(read_m3u(str(loved_playlist)))
            unplaylisted = sorted(loved_tracks - playlisted_tracks)
            
            if not unplaylisted:
                self.set_status("No unplaylisted tracks found")
                return False
                
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_playlist = self.playlists_dir / f"Unplaylisted_{timestamp}.m3u"
            write_m3u(str(new_playlist), unplaylisted)
            
            import subprocess
            subprocess.Popen(['C:\\Program Files (x86)\\Dopamine\\Dopamine.exe', str(new_playlist)])
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to collect unplaylisted: {e}", exc_info=True)
            self.report_error(f"Failed to collect unplaylisted: {str(e)}")
            return False

    def cache_current_state(self) -> bool:
        """Cache current song and file selection state."""
        if not (self.current_song and self.current_file):
            return False
        self.save_state('curation')
        return True

    def restore_cached_state(self) -> bool:
        """Restore cached song and file selection state."""
        if self.load_state('curation'):
            if self.current_song and self.current_file:
                self.song_changed.emit(self.current_song)
                self.file_selection_changed.emit(self.current_file)
                return True
        return False