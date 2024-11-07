# gui/windows/pages/maintenance/handlers/delete_handler.py

from pathlib import Path
import logging
from PyQt6.QtWidgets import QMessageBox, QApplication
from core.playlist.safety import PlaylistSafety
from app.config import Config

class DeleteHandler:
    """Handles playlist deletion operations with safety checks."""
    
    def __init__(self, state):
        self.state = state
        self.logger = logging.getLogger('delete_handler')
        self.safety = PlaylistSafety(Path(Config.BACKUP_DIR))
        
    def delete_playlist(self, playlist_path: Path):
        """Delete a playlist with safety checks and backups."""
        try:
            # Get the active window as parent for dialogs
            active_window = QApplication.activeWindow()
            
            # Show confirmation dialog
            response = QMessageBox.warning(
                active_window,
                "Confirm Playlist Deletion",
                f"Are you sure you want to delete '{playlist_path.name}'?\n\n"
                "This operation will create a backup, but the playlist will be removed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if response != QMessageBox.StandardButton.Yes:
                self.logger.info("Deletion cancelled by user")
                return
            
            self.state.delete_started.emit(playlist_path)
            self.state.set_status(f"Creating backup of {playlist_path.name}...")
            
            # Create backup
            backup_path = self.safety.create_backup(playlist_path)
            if not backup_path:
                self.state.report_error("Failed to create backup")
                return
                
            # Show backup notification
            QMessageBox.information(
                active_window,
                "Backup Created",
                f"A backup has been created at:\n{backup_path}",
                QMessageBox.StandardButton.Ok
            )
            
            # Delete playlist
            self.state.set_status(f"Deleting {playlist_path.name}...")
            playlist_path.unlink()
            
            if playlist_path.exists():
                self.state.report_error("Failed to delete playlist")
                return
                
            # Emit completion signal
            self.state.delete_completed.emit()
            self.state.set_status("Playlist deleted successfully")
            
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            self.state.report_error(f"Delete failed: {str(e)}")
            
    def cleanup(self):
        """Clean up resources."""
        pass