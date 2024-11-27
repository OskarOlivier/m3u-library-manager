# gui/windows/pages/maintenance/state.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set
from PyQt6.QtCore import QObject, pyqtSignal
import logging

@dataclass
class PlaylistAnalysis:
    """Stores analysis results for a playlist."""
    missing_files: Set[Path]
    sort_method: Optional[str]
    has_duplicates: bool
    total_files: int
    valid_files: int
    exists_remotely: bool = True

    @property
    def has_differences(self) -> bool:
        """Check if playlist has any differences that need attention."""
        return bool(self.missing_files or self.has_duplicates)
        
    def has_errors(self) -> bool:
        """Check if analysis found any issues."""
        return bool(self.missing_files or self.has_duplicates)

class MaintenanceState(QObject):
    """State management for maintenance page."""
    
    # Analysis signals
    analysis_started = pyqtSignal(Path)  # Path to playlist being analyzed
    analysis_completed = pyqtSignal(Path, object)  # Path and analysis results
    analysis_all_started = pyqtSignal()
    analysis_all_completed = pyqtSignal()
    
    # Selection signals
    playlist_selected = pyqtSignal(Path)
    playlist_deselected = pyqtSignal()
    
    delete_completed = pyqtSignal()
    
    repair_completed = pyqtSignal()
    
    status_changed = pyqtSignal(object)
    progress_updated = pyqtSignal(object)
    
    error_occurred = pyqtSignal()

    
    def __init__(self):
        super().__init__()
        self.current_playlist: Optional[Path] = None
        self.analyses: Dict[Path, PlaylistAnalysis] = {}
        self.is_analyzing = False
        self.logger = logging.getLogger('maintenance_state')
        
    def set_current_playlist(self, playlist: Optional[Path]) -> None:
        """Update current playlist selection."""
        if playlist != self.current_playlist:
            old_playlist = self.current_playlist
            self.current_playlist = playlist
            
            if old_playlist:
                self.playlist_deselected.emit()
                
            if playlist is not None:
                self.playlist_selected.emit(playlist)
                # Re-emit analysis result if available
                if playlist in self.analyses:
                    self.logger.debug(f"Re-emitting cached analysis for {playlist.name}")
                    self.analysis_completed.emit(playlist, self.analyses[playlist])
    
    def get_analysis(self, playlist: Path) -> Optional[PlaylistAnalysis]:
        """Get analysis results for a playlist if available."""
        result = self.analyses.get(playlist)
        if result:
            self.logger.debug(f"Retrieved cached analysis for {playlist.name}")
            self.logger.debug(f"Sort method: {result.sort_method}")
        return result
    
    def set_analysis(self, playlist: Path, analysis: PlaylistAnalysis) -> None:
        """Store analysis results for a playlist."""
        self.logger.debug(f"Caching analysis for {playlist.name}")
        self.logger.debug(f"Sort method: {analysis.sort_method}")
        self.analyses[playlist] = analysis
        self.analysis_completed.emit(playlist, analysis)
        
    def clear_analysis(self, playlist: Path) -> None:
        """Clear analysis results for a playlist."""
        if playlist in self.analyses:
            del self.analyses[playlist]
            
    def clear_all_analyses(self) -> None:
        """Clear all analysis results."""
        self.analyses.clear()
        
    def update_progress(self, value: int) -> None:
        """Update progress value."""
        self.progress_updated.emit(value)
        
    def set_status(self, status: str) -> None:
        """Update status message."""
        self.status_changed.emit(status)
        
    def report_error(self, error: str) -> None:
        """Report an error condition."""
        self.error_occurred.emit(error)
        self.set_status(f"Error: {error}")
        
    def get_current_progress(self) -> int:
        """Get current progress percentage."""
        return 0 if not self.is_analyzing else -1  # -1 indicates indeterminate
        
    def is_playlist_analyzed(self, playlist: Path) -> bool:
        """Check if a playlist has been analyzed."""
        return playlist in self.analyses
        
    def get_failed_playlists(self) -> Set[Path]:
        """Get set of playlists that had analysis errors."""
        return {
            playlist for playlist, analysis in self.analyses.items()
            if analysis.has_errors()
        }
        
    def finish_analysis(self):
        """Complete the analysis process."""
        self.is_analyzing = False
        self.analysis_all_completed.emit()