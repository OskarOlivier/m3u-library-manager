# gui/windows/pages/sync/state.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set
from PyQt6.QtCore import pyqtSignal
import json

from core.state.base_state import BaseState

@dataclass
class PlaylistAnalysis:
    """Stores analysis results for a playlist."""
    missing_remotely: Set[Path]
    missing_locally: Set[Path]
    exists_remotely: bool
    
    @property 
    def is_synced(self) -> bool:
        return (self.exists_remotely and 
                len(self.missing_remotely) == 0 and 
                len(self.missing_locally) == 0)
    
    @property
    def has_differences(self) -> bool:
        return len(self.missing_remotely) > 0 or len(self.missing_locally) > 0

@dataclass
class SyncStateData:
    """Serializable sync state data."""
    current_playlist: Optional[str] = None
    analyses: Dict[str, dict] = None  # Serialized PlaylistAnalysis objects
    total_playlists: int = 0
    analyzed_playlists: int = 0

class SyncPageState(BaseState[SyncStateData]):
    """Manages state and signals for sync page components."""
    
    # Analysis signals
    analysis_started = pyqtSignal(Path)
    analysis_completed = pyqtSignal(Path, object)
    analysis_all_started = pyqtSignal()
    analysis_all_completed = pyqtSignal()
    
    # Selection signals
    playlist_selected = pyqtSignal(Path)
    playlist_deselected = pyqtSignal()
    
    # Sync signals
    sync_started = pyqtSignal(str)  # Operation type
    sync_completed = pyqtSignal()
    sync_progress = pyqtSignal(int)  # Progress percentage
    
    def __init__(self):
        super().__init__()
        self.current_playlist: Optional[Path] = None
        self.analyses: Dict[Path, PlaylistAnalysis] = {}
        self.is_analyzing = False
        self.is_syncing = False
        self.total_playlists = 0
        self.analyzed_playlists = 0
        self.playlists_dir: Optional[Path] = None

    async def _do_initialize(self) -> None:
        """Initialize state data."""
        await super()._do_initialize()
        self.set_status("Sync state initialized")

    def _do_reset(self) -> None:
        """Reset state to initial values."""
        self.current_playlist = None
        self.analyses.clear()
        self.is_analyzing = False
        self.is_syncing = False
        self.total_playlists = 0
        self.analyzed_playlists = 0

    def _get_serializable_state(self) -> dict:
        """Convert state to serializable format."""
        return {
            'current_playlist': str(self.current_playlist) if self.current_playlist else None,
            'analyses': {
                str(path): self._serialize_analysis(analysis)
                for path, analysis in self.analyses.items()
            },
            'total_playlists': self.total_playlists,
            'analyzed_playlists': self.analyzed_playlists
        }

    def _restore_from_state(self, state_data: dict) -> None:
        """Restore state from serialized data."""
        if state_data.get('current_playlist'):
            self.current_playlist = Path(state_data['current_playlist'])
            
        self.analyses = {
            Path(path): self._deserialize_analysis(data)
            for path, data in state_data.get('analyses', {}).items()
        }
        
        self.total_playlists = state_data.get('total_playlists', 0)
        self.analyzed_playlists = state_data.get('analyzed_playlists', 0)
        
        # Re-emit signals for restored state
        if self.current_playlist:
            self.playlist_selected.emit(self.current_playlist)

    def _serialize_analysis(self, analysis: PlaylistAnalysis) -> dict:
        """Convert PlaylistAnalysis to serializable format."""
        return {
            'missing_remotely': [str(p) for p in analysis.missing_remotely],
            'missing_locally': [str(p) for p in analysis.missing_locally],
            'exists_remotely': analysis.exists_remotely
        }

    def _deserialize_analysis(self, data: dict) -> PlaylistAnalysis:
        """Create PlaylistAnalysis from serialized data."""
        return PlaylistAnalysis(
            missing_remotely={Path(p) for p in data['missing_remotely']},
            missing_locally={Path(p) for p in data['missing_locally']},
            exists_remotely=data['exists_remotely']
        )

    def set_current_playlist(self, playlist: Optional[Path], emit: bool = True) -> None:
        """Update current playlist selection."""
        if playlist != self.current_playlist:
            self.current_playlist = playlist
            
            if emit:
                if playlist is not None:
                    self.playlist_selected.emit(playlist)
                else:
                    self.playlist_deselected.emit()

    def get_analysis(self, playlist: Path) -> Optional[PlaylistAnalysis]:
        """Get analysis results for a playlist if available."""
        return self.analyses.get(playlist)

    def set_analysis(self, playlist_path: Path, analysis: PlaylistAnalysis) -> None:
        """Store analysis results for a playlist."""
        self.analyses[playlist_path] = analysis
        self.analysis_completed.emit(playlist_path, analysis)
        
        # If this is the current playlist, re-emit selection
        if playlist_path == self.current_playlist:
            self.playlist_selected.emit(playlist_path)

    def start_sync(self, operation: str):
        """Start a sync operation."""
        self.is_syncing = True
        self.sync_started.emit(operation)
        self.set_status(f"Starting {operation} operation...")

    def finish_sync(self):
        """Complete the sync operation."""
        self.is_syncing = False
        self.sync_completed.emit()
        self.update_progress(100)
        self.set_status("Sync operation completed")

    def start_bulk_analysis(self, total: int):
        """Start bulk analysis with total count."""
        self.total_playlists = total
        self.analyzed_playlists = 0
        self.analysis_all_started.emit()
        self.set_status(f"Analyzing {total} playlists...")

    def update_analysis_progress(self, playlist: Path):
        """Update bulk analysis progress."""
        self.analyzed_playlists += 1
        progress = int((self.analyzed_playlists / self.total_playlists) * 100)
        self.update_progress(progress)

    def finish_analysis(self):
        """Complete the analysis process."""
        self.is_analyzing = False
        self.total_playlists = 0
        self.analyzed_playlists = 0
        self.analysis_all_completed.emit()
        self.update_progress(100)

    def is_playlist_uploadable(self, playlist_path: Path) -> bool:
        """Check if a playlist can be uploaded."""
        if not playlist_path:
            return False
        analysis = self.get_analysis(playlist_path)
        return analysis is not None and not analysis.exists_remotely
        
    def cache_current_state(self) -> bool:
        """
        Cache current playlist and analysis state.
        
        Returns:
            bool: True if state was cached, False if nothing to cache
        """
        if not (self.current_playlist or self.analyses):
            return False
            
        # Save state to cache file
        self.save_state('sync')
        return True

    def restore_cached_state(self) -> bool:
        """
        Restore cached playlist and analysis state.
        
        Returns:
            bool: True if state was restored, False if no cache exists
        """
        if self.load_state('sync'):
            if self.current_playlist:
                self.playlist_selected.emit(self.current_playlist)
            return True
        return False