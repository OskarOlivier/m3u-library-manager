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
    exists_remotely: bool
    
    @property
    def is_synced(self) -> bool:
        """Check if playlist is fully synced."""
        return (self.exists_remotely and 
                len(self.missing_remotely) == 0 and 
                len(self.missing_locally) == 0)
    
    @property
    def has_differences(self) -> bool:
        """Check if playlist has any differences."""
        return len(self.missing_remotely) > 0 or len(self.missing_locally) > 0
        
@dataclass
class AnalysisProgress:
    """Stores analysis progress information."""
    total_playlists: int = 0
    completed_playlists: int = 0
    current_playlist: Optional[Path] = None
    
    @property
    def percentage(self) -> int:
        """Calculate total percentage progress."""
        if self.total_playlists == 0:
            return 0
        return int((self.completed_playlists / self.total_playlists) * 100)
        
    def reset(self):
        """Reset progress tracking."""
        self.total_playlists = 0
        self.completed_playlists = 0
        self.current_playlist = None

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
        self.analysis_progress = AnalysisProgress()
        
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
        
    def start_bulk_analysis(self, total_playlists: int):
        """Initialize bulk analysis progress."""
        self.analysis_progress = AnalysisProgress(total_playlists=total_playlists)
        self.is_analyzing = True
        self.update_analysis_status()
        self.analysis_all_started.emit()
        
    def update_analysis_progress(self, playlist: Path):
        """Update analysis progress."""
        self.analysis_progress.current_playlist = playlist
        self.analysis_progress.completed_playlists += 1
        self.update_progress(self.analysis_progress.percentage)
        self.update_analysis_status()
        
    def update_analysis_status(self):
        """Update status message for analysis."""
        if not self.is_analyzing:
            return
            
        if self.analysis_progress.current_playlist:
            status = (
                f"Analyzing {self.analysis_progress.current_playlist.name} "
                f"({self.analysis_progress.completed_playlists}/{self.analysis_progress.total_playlists})"
            )
            self.set_status(status)
            
    def finish_analysis(self):
        """Complete the analysis process."""
        self.is_analyzing = False
        self.analysis_progress.reset()
        self.analysis_all_completed.emit()
        
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
        
    def get_current_progress(self) -> int:
        """Get current progress percentage."""
        return self.analysis_progress.percentage if self.is_analyzing else 0
        
    def is_playlist_analyzed(self, playlist: Path) -> bool:
        """Check if a playlist has been analyzed."""
        return playlist in self.analyses
        
    def get_failed_playlists(self) -> Set[Path]:
        """Get set of playlists that failed analysis."""
        return {
            playlist for playlist, analysis in self.analyses.items()
            if not analysis.exists_remotely
        }