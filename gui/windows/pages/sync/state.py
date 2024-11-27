# gui/windows/pages/sync/state.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set
from PyQt6.QtCore import QObject, pyqtSignal
import logging

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
        """Check if playlist has any differences that need syncing."""
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
    sync_progress = pyqtSignal(int)  # Progress percentage
    
    # Status signals
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
        
    def __init__(self):
        super().__init__()
        self.current_playlist: Optional[Path] = None
        self.analyses: Dict[Path, PlaylistAnalysis] = {}
        self.is_analyzing = False
        self.is_syncing = False
        self.total_playlists = 0
        self.analyzed_playlists = 0
        self.playlists_dir: Optional[Path] = None
        self.logger = logging.getLogger('sync_state')
        self.logger.setLevel(logging.DEBUG)
        
    def set_current_playlist(self, playlist: Optional[Path], emit: bool = True) -> None:
        """Update current playlist selection."""
        if playlist != self.current_playlist:
            self.logger.debug(f"Updating current playlist: {playlist}")
            old_playlist = self.current_playlist
            self.current_playlist = playlist
            
            if emit:
                if playlist is not None:
                    self.logger.debug(f"Emitting playlist_selected for: {playlist}")
                    self.playlist_selected.emit(playlist)
                    
                    # Log cached analysis state if available
                    if playlist in self.analyses:
                        analysis = self.analyses[playlist]
                        self.logger.debug(f"Found cached analysis - Remote: {len(analysis.missing_remotely)}, "
                                        f"Local: {len(analysis.missing_locally)}")
                    else:
                        self.logger.debug("No cached analysis found for newly selected playlist")
                else:
                    self.logger.debug("Emitting playlist_deselected")
                    self.playlist_deselected.emit()
                
    def get_analysis(self, playlist: Path) -> Optional[PlaylistAnalysis]:
        """Get analysis results for a playlist if available."""
        result = self.analyses.get(playlist)
        if result:
            self.logger.debug(f"Retrieved analysis for {playlist.name} - "
                            f"Remote: {len(result.missing_remotely)}, "
                            f"Local: {len(result.missing_locally)}")
        else:
            self.logger.debug(f"No analysis found for {playlist.name}")
        return result
    
    def set_analysis(self, playlist_path: Path, analysis: PlaylistAnalysis) -> None:
        """Store analysis results for a playlist."""
        self.logger.debug(f"Storing analysis for {playlist_path.name}")
        self.logger.debug(f"Analysis details - Remote: {len(analysis.missing_remotely)}, "
                         f"Local: {len(analysis.missing_locally)}, "
                         f"Exists remotely: {analysis.exists_remotely}")
        
        self.analyses[playlist_path] = analysis
        
        # If this is the currently selected playlist, re-emit selection to trigger update
        if playlist_path == self.current_playlist:
            self.logger.debug("Analysis completed for currently selected playlist - triggering update")
            # First emit analysis completion
            self.analysis_completed.emit(playlist_path, analysis)
            # Then re-emit selection to ensure panels update
            self.playlist_selected.emit(playlist_path)
        else:
            # Just emit analysis completion for non-selected playlists
            self.analysis_completed.emit(playlist_path, analysis)

    def start_sync(self, operation: str):
        """Start a sync operation."""
        self.logger.debug(f"Starting sync operation: {operation}")
        self.is_syncing = True
        self.sync_started.emit(operation)
        self.set_status(f"Starting {operation} operation...")

    def finish_sync(self):
        """Complete the sync operation."""
        self.logger.debug("Finishing sync operation")
        self.is_syncing = False
        self.sync_completed.emit()
        self.update_progress(100)
        self.set_status("Sync operation completed")
        
    def clear_analysis(self, playlist: Path) -> None:
        """Clear analysis results for a playlist."""
        if playlist in self.analyses:
            self.logger.debug(f"Clearing analysis for {playlist.name}")
            del self.analyses[playlist]
            
    def clear_all_analyses(self) -> None:
        """Clear all analysis results."""
        self.logger.debug(f"Clearing all analyses ({len(self.analyses)} entries)")
        self.analyses.clear()
        
    def update_progress(self, value: int) -> None:
        """Update progress value."""
        self.progress_updated.emit(value)
        self.sync_progress.emit(value)
        
    def set_status(self, status: str) -> None:
        """Update status message."""
        self.logger.debug(f"Status: {status}")
        self.status_changed.emit(status)
        
    def report_error(self, error: str) -> None:
        """Report an error condition."""
        self.logger.error(f"Error: {error}")
        self.error_occurred.emit(error)
        self.set_status(f"Error: {error}")
        
    def start_bulk_analysis(self, total: int):
        """Start bulk analysis with total count."""
        self.logger.debug(f"Starting bulk analysis of {total} playlists")
        self.total_playlists = total
        self.analyzed_playlists = 0
        self.analysis_all_started.emit()
        self.set_status(f"Analyzing {total} playlists...")

    def update_analysis_progress(self, playlist: Path):
        """Update bulk analysis progress."""
        self.analyzed_playlists += 1
        progress = int((self.analyzed_playlists / self.total_playlists) * 100)
        self.logger.debug(f"Analysis progress: {self.analyzed_playlists}/{self.total_playlists} "
                         f"({progress}%) - Current: {playlist.name}")
        self.update_progress(progress)

    def finish_analysis(self):
        """Complete the analysis process."""
        self.logger.debug("Finishing analysis process")
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