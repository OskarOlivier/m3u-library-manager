# gui/windows/pages/maintenance/state.py
"""State management for maintenance operations."""

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
    
    def __init__(self):
        super().__init__()
        # Basic properties
        self.current_playlist: Optional[Path] = None
        self.analyses: Dict[Path, FileAnalysis] = {}
        
        # Initialize all signals
        self._init_signals()
        
    def _init_signals(self):
        """Initialize all signals with proper types."""
        # Analysis signals
        self.analysis_started = pyqtSignal(str)  # Path as string
        self.analysis_completed = pyqtSignal(str, object)  # Path as string, FileAnalysis as object
        
        # File location signals
        self.location_started = pyqtSignal()
        self.location_completed = pyqtSignal(object)  # List[Path] as object
        
        # Sort signals
        self.sort_started = pyqtSignal(str)  # Sort criteria
        self.sort_completed = pyqtSignal()
        
        # Delete signals
        self.delete_started = pyqtSignal(str)  # Path as string
        self.delete_completed = pyqtSignal()
        
        # Selection signals
        self.playlist_selected = pyqtSignal(str)  # Path as string
        self.playlist_deselected = pyqtSignal()
        
        # Progress and status
        self.progress_updated = pyqtSignal(int)
        self.status_changed = pyqtSignal(str)
        self.error_occurred = pyqtSignal(str)
        
    def set_current_playlist(self, playlist: Optional[Path]):
        """Update current playlist selection."""
        if playlist != self.current_playlist:
            self.current_playlist = playlist
            if playlist is not None:
                self.playlist_selected.emit(str(playlist))
            else:
                self.playlist_deselected.emit()
                
    def get_analysis(self, playlist: Path) -> Optional[FileAnalysis]:
        """Get analysis for a playlist if available."""
        return self.analyses.get(playlist)
        
    def set_analysis(self, playlist: Path, analysis: FileAnalysis):
        """Store analysis results."""
        self.analyses[playlist] = analysis
        self.analysis_completed.emit(str(playlist), analysis)
        
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