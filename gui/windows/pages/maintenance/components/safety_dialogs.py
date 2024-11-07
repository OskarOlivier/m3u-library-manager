# gui/windows/pages/maintenance/components/safety_dialogs.py

from PyQt6.QtWidgets import QMessageBox
from pathlib import Path

class SafetyDialogs:
    """Safety confirmation dialogs for maintenance operations."""
    
    @staticmethod
    def get_active_window():
        """Get the current active window for dialog parenting."""
        return QApplication.activeWindow()
    
    @staticmethod
    def confirm_playlist_delete(playlist_name: str) -> bool:
        """Show confirmation dialog for playlist deletion."""
        parent = SafetyDialogs.get_active_window()
        response = QMessageBox.warning(
            parent,
            "Confirm Playlist Deletion",
            f"Are you sure you want to delete '{playlist_name}'?\n\n"
            "This operation will create a backup, but the playlist will be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def show_backup_created(backup_path: Path):
        """Show notification of backup creation."""
        parent = SafetyDialogs.get_active_window()
        QMessageBox.information(
            parent,
            "Backup Created",
            f"A backup has been created at:\n{backup_path}\n\n"
            "You can find all backups in the backups folder.",
            QMessageBox.StandardButton.Ok
        )
        
    @staticmethod
    def confirm_sort_playlist(playlist_name: str) -> bool:
        """
        Show confirmation dialog for playlist sorting.
        
        Args:
            playlist_name: Name of playlist to sort
            
        Returns:
            bool: True if user confirmed
        """
        response = QMessageBox.question(
            None,
            "Confirm Playlist Sort",
            f"Sort playlist '{playlist_name}'?\n\n"
            "This will reorder all entries. A backup will be created first.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes
        
    @staticmethod
    def confirm_bulk_operation(operation: str, count: int) -> bool:
        """
        Show confirmation dialog for bulk operations.
        
        Args:
            operation: Name of operation
            count: Number of items affected
            
        Returns:
            bool: True if user confirmed
        """
        response = QMessageBox.question(
            None,
            f"Confirm {operation}",
            f"This will {operation.lower()} {count} items.\n\n"
            "Backups will be created for all affected playlists.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes
        
    @staticmethod
    def confirm_restore_backup(backup_name: str) -> bool:
        """
        Show confirmation dialog for backup restoration.
        
        Args:
            backup_name: Name of backup to restore
            
        Returns:
            bool: True if user confirmed
        """
        response = QMessageBox.warning(
            None,
            "Confirm Restore Backup",
            f"Restore from backup '{backup_name}'?\n\n"
            "This will replace the current playlist content.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes