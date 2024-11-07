# gui/windows/pages/maintenance/state.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict
from PyQt6.QtCore import QObject, pyqtSignal

@dataclass
class FileAnalysis:
    """Analysis results for a playlist's files."""
    missing_files: List[Path]
    found_files: List[Path]
    invalid_paths: List[str]

class MaintenanceState(QObject):
    """State management for maintenance page."""
    
    # Analysis signals
    analysis_started = pyqtSignal(Path)
    analysis_completed = pyqtSignal(Path, object)  # Path and FileAnalysis
    analysis_all_started = pyqtSignal()
    analysis_all_completed = pyqtSignal()
    
    # File location signals
    location_started = pyqtSignal(list)  # List of files
    location_completed = pyqtSignal(list)  # List of found files
    
    # Sort signals
    sort_started = pyqtSignal(str)  # Sort criteria
    sort_completed = pyqtSignal()
    
    # Delete signals
    delete_started = pyqtSignal(Path)
    delete_completed = pyqtSignal()
    
    # Selection signals
    playlist_selected = pyqtSignal(Path)
    playlist_deselected = pyqtSignal()
    
    # Operation signals
    operation_started = pyqtSignal(str)  # Operation name
    operation_completed = pyqtSignal(str, bool)  # Operation name, success
    
    # Progress and status
    progress_updated = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_playlist: Optional[Path] = None
        self.analyses: Dict[Path, FileAnalysis] = {}
        self.is_analyzing = False
        self.is_busy = False
        
    def set_current_playlist(self, playlist: Optional[Path]):
        """Update current playlist selection."""
        if playlist != self.current_playlist:
            self.current_playlist = playlist
            if playlist is not None:
                self.playlist_selected.emit(playlist)
            else:
                self.playlist_deselected.emit()
                
    def get_analysis(self, playlist: Path) -> Optional[FileAnalysis]:
        """Get analysis for a playlist if available."""
        return self.analyses.get(playlist)
        
    def set_analysis(self, playlist: Path, analysis: FileAnalysis):
        """Store analysis results."""
        self.analyses[playlist] = analysis
        self.analysis_completed.emit(playlist, analysis)
        
    def update_progress(self, value: int):
        """Update progress value."""
        self.progress_updated.emit(value)
        
    def set_status(self, status: str):
        """Update status message."""
        self.status_changed.emit(status)
        
    def report_error(self, error: str):
        """Report an error condition."""
        self.error_occurred.emit(error)
        self.set_status(f"Error: {error}")
        
    def clear_analysis(self, playlist: Path):
        """Clear analysis results for a playlist."""
        if playlist in self.analyses:
            del self.analyses[playlist]
            
    def clear_all_analyses(self):
        """Clear all analysis results."""
        self.analyses.clear()