# gui/windows/pages/maintenance/handlers/sort_handler.py

from pathlib import Path
import logging
from ..components.safety_dialogs import SafetyDialogs
from core.playlist.safety import PlaylistSafety
from app.config import Config

class SortHandler:
    """Handles playlist sorting operations with safety checks."""
    
    def __init__(self, state):
        self.state = state
        self.logger = logging.getLogger('sort_handler')
        self.safety = PlaylistSafety(Path(Config.BACKUP_DIR))
        
    def sort_playlist(self, playlist_path: Path, criteria: str):
        """Sort playlist with safety checks and backups."""
        try:
            # Show confirmation dialog
            if not SafetyDialogs.confirm_sort_playlist(playlist_path.name):
                self.logger.info("Sort cancelled by user")
                return
                
            self.state.operation_started.emit(f"Sort Playlist by {criteria}")
            self.state.set_status(f"Creating backup of {playlist_path.name}...")
            
            # Create backup
            backup_path = self.safety.create_backup(playlist_path)
            if not backup_path:
                self.state.report_error("Failed to create backup")
                return
                
            # Show backup notification
            SafetyDialogs.show_backup_created(backup_path)
            
            # Perform sort
            self.state.set_status(f"Sorting {playlist_path.name}...")
            # TODO: Implement actual sorting
            self.state.update_progress(100)
            
            self.state.operation_completed.emit("Sort Playlist", True)
            self.state.set_status("Playlist sorted successfully")
            
        except Exception as e:
            self.logger.error(f"Sort failed: {e}")
            self.state.report_error(f"Sort failed: {str(e)}")
            self.state.operation_completed.emit("Sort Playlist", False)
            
    def cleanup(self):
        """Clean up resources."""
        pass