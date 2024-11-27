# gui/windows/pages/maintenance/handlers/delete_handler.py

from pathlib import Path
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

from core.playlist.safety import PlaylistSafety
from app.config import Config
from gui.dialogs.safety_dialogs import SafetyDialogs

class DeleteHandler(QObject):
    """Handles playlist deletion operations with safety checks."""
    
    # Signals
    operation_started = pyqtSignal(str)  # Operation description
    operation_completed = pyqtSignal(bool)  # Success status
    progress_updated = pyqtSignal(int)  # Progress value
    status_updated = pyqtSignal(str)  # Status message
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('delete_handler')
        self.safety = PlaylistSafety(Path(Config.BACKUP_DIR))
        
    def delete_playlist(self, playlist_path: Path) -> None:
        """
        Delete a playlist with safety checks and backups.
        
        Args:
            playlist_path: Path to playlist to delete
        """
        try:
            # Get confirmation
            if not SafetyDialogs.confirm_playlist_delete(playlist_path.name):
                self.logger.info("Deletion cancelled by user")
                return
                
            # Start operation
            self.operation_started.emit("Delete Playlist")
            self.status_updated.emit(f"Creating backup of {playlist_path.name}...")
            self.progress_updated.emit(25)
            
            # Create backup
            backup_path = self.safety.create_backup(playlist_path)
            if not backup_path:
                self.error_occurred.emit("Failed to create backup")
                self.operation_completed.emit(False)
                return
                
            # Show backup notification
            SafetyDialogs.show_backup_created(backup_path)
            self.progress_updated.emit(50)
            
            # Delete playlist
            self.status_updated.emit(f"Deleting {playlist_path.name}...")
            playlist_path.unlink()
            
            if playlist_path.exists():
                self.error_occurred.emit("Failed to delete playlist")
                self.operation_completed.emit(False)
                return
                
            # Success
            self.progress_updated.emit(100)
            self.status_updated.emit("Playlist deleted successfully")
            self.operation_completed.emit(True)
            
        except Exception as e:
            self.logger.error(f"Delete failed: {e}", exc_info=True)
            self.error_occurred.emit(f"Delete failed: {str(e)}")
            self.operation_completed.emit(False)
            
    def cleanup(self):
        """Clean up any resources."""
        pass