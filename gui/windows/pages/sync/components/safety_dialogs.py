# gui/windows/pages/sync/components/safety_dialogs.py

from PyQt6.QtWidgets import QMessageBox
from pathlib import Path

class SafetyDialogs:
    """Safety confirmation dialogs for sync operations."""
    
    @staticmethod
    def confirm_delete_files(location: str, count: int) -> bool:
        """
        Show confirmation dialog for file deletion.
        
        Args:
            location: 'local' or 'remote' location
            count: Number of files to delete
            
        Returns:
            bool: True if user confirmed
        """
        response = QMessageBox.warning(
            None,
            f"Confirm Delete from {location.title()}",
            f"Are you sure you want to delete {count} files from the {location} location?\n\n"
            "This operation cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes

    @staticmethod
    def confirm_sync_operation(operation: str, count: int) -> bool:
        """
        Show confirmation dialog for sync operations.
        
        Args:
            operation: Type of sync operation
            count: Number of files affected
            
        Returns:
            bool: True if user confirmed
        """
        response = QMessageBox.question(
            None,
            "Confirm Sync Operation",
            f"This will {operation} {count} files.\n\n"
            "A backup will be created before proceeding.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes

    @staticmethod
    def show_backup_created(backup_path: Path):
        """Show notification of backup creation."""
        QMessageBox.information(
            None,
            "Backup Created",
            f"A backup has been created at:\n{backup_path}\n\n"
            "You can find all backups in the backups folder.",
            QMessageBox.StandardButton.Ok
        )

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
            f"This will {operation.lower()} {count} files.\n\n"
            "Backups will be created for all affected playlists.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes