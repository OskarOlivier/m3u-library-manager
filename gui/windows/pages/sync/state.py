# gui/windows/pages/sync/state.py

"""State management for sync page."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set, Dict
from PyQt6.QtCore import QObject, pyqtSignal

@dataclass
class PlaylistAnalysis:
    """Stores analysis results for a playlist."""
    missing_remotely: Set[Path]
    missing_locally: Set[Path]
    is_synced: bool
    exists_remotely: bool
    
    @property
    def has_differences(self) -> bool:
        """Check if playlist has any differences."""
        return len(self.missing_remotely) > 0 or len(self.missing_locally) > 0

class SyncPageState(QObject):
    """Manages state and signals for sync page components."""
    
    # Analysis signals
    analysis_started = pyqtSignal(Path)  # Emitted when analysis begins
    analysis_completed = pyqtSignal(Path, object)  # Emitted with results
    analysis_all_started = pyqtSignal()
    analysis_all_completed = pyqtSignal()
    
    # Selection signals
    playlist_selected = pyqtSignal(Path)
    playlist_deselected = pyqtSignal()
    
    # Sync signals
    sync_started = pyqtSignal(str)  # Operation type
    sync_completed = pyqtSignal()
    
    # Progress and status
    progress_updated = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_playlist: Optional[Path] = None
        self.analyses: Dict[Path, PlaylistAnalysis] = {}
        self.is_analyzing = False
        self.is_syncing = False
        
    def set_current_playlist(self, playlist: Optional[Path]) -> None:
        """Update current playlist selection."""
        if playlist != self.current_playlist:
            self.current_playlist = playlist
            if playlist is not None:
                self.playlist_selected.emit(playlist)
            else:
                self.playlist_deselected.emit()
                
    def get_analysis(self, playlist: Path) -> Optional[PlaylistAnalysis]:
        """Get analysis results for a playlist if available."""
        return self.analyses.get(playlist)
    
    def set_analysis(self, playlist: Path, analysis: PlaylistAnalysis) -> None:
        """Store analysis results for a playlist."""
        self.analyses[playlist] = analysis
        self.analysis_completed.emit(playlist, analysis)
        
    def clear_analysis(self, playlist: Path) -> None:
        """Clear analysis results for a playlist."""
        if playlist in self.analyses:
            del self.analyses[playlist]
            
    def clear_all_analyses(self) -> None:
        """Clear all analysis results."""
        self.analyses.clear()
        
    def set_status(self, status: str) -> None:
        """Update status message."""
        self.status_changed.emit(status)
        
    def report_error(self, error: str) -> None:
        """Report an error condition."""
        self.error_occurred.emit(error)
        self.set_status(f"Error: {error}")
        
    def update_progress(self, progress: int) -> None:
        """Update progress value."""
        self.progress_updated.emit(progress)