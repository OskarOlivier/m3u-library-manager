# gui/dialogs/safety_dialogs.py

from pathlib import Path
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from .base_dialog import BaseDialog

class ErrorDialog(BaseDialog):
    """Dialog for displaying errors."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(title, parent)
        
        error_label = QLabel()
        error_label.setPixmap(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_MessageBoxCritical
        ).pixmap(32, 32))
        
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        
        self.content_layout.addWidget(error_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.addWidget(message_label)
        
        # Only need OK button
        self.cancel_btn.hide()
        self.ok_btn.setText("OK")

class DeleteConfirmDialog(BaseDialog):
    """Dialog for confirming file deletion."""
    
    def __init__(self, location: str, count: int, parent=None):
        super().__init__(f"Confirm Delete from {location.title()}", parent)
        
        # Warning icon and message
        warning_label = QLabel()
        warning_label.setPixmap(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_MessageBoxWarning
        ).pixmap(32, 32))
        
        message = QLabel(
            f"Are you sure you want to delete {count} files from the {location} location?\n\n"
            "This operation cannot be undone."
        )
        message.setWordWrap(True)
        
        # Add to content layout
        self.content_layout.addWidget(warning_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.addWidget(message)
        
        # Update button text
        self.ok_btn.setText("Delete")
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #E81123;
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #F1707A;
            }
            QPushButton:pressed {
                background-color: #D20F1F;
            }
        """)

class SyncConfirmDialog(BaseDialog):
    """Dialog for confirming sync operations."""
    
    def __init__(self, operation: str, count: int, parent=None):
        super().__init__("Confirm Sync Operation", parent)
        
        message = QLabel(
            f"This will {operation} {count} files.\n\n"
            "A backup will be created before proceeding."
        )
        message.setWordWrap(True)
        
        self.content_layout.addWidget(message)
        
        # Update button text
        self.ok_btn.setText("Sync")

class BackupCreatedDialog(BaseDialog):
    """Dialog showing backup creation notification."""
    
    def __init__(self, backup_path: Path, parent=None):
        super().__init__("Backup Created", parent)
        
        info_label = QLabel()
        info_label.setPixmap(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_MessageBoxInformation
        ).pixmap(32, 32))
        
        message = QLabel(
            f"A backup has been created at:\n{backup_path}\n\n"
            "You can find all backups in the backups folder."
        )
        message.setWordWrap(True)
        
        self.content_layout.addWidget(info_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.addWidget(message)
        
        # Only need OK button
        self.cancel_btn.hide()
        self.ok_btn.setText("OK")

class BulkOperationDialog(BaseDialog):
    """Dialog for confirming bulk operations."""
    
    def __init__(self, operation: str, count: int, parent=None):
        super().__init__(f"Confirm {operation}", parent)
        
        message = QLabel(
            f"This will {operation.lower()} {count} files.\n\n"
            "Backups will be created for all affected playlists."
        )
        message.setWordWrap(True)
        
        self.content_layout.addWidget(message)
        
        # Update button text
        self.ok_btn.setText("Proceed")

class RestoreBackupDialog(BaseDialog):
    """Dialog for confirming backup restoration."""
    
    def __init__(self, backup_name: str, parent=None):
        super().__init__("Confirm Restore Backup", parent)
        
        warning_label = QLabel()
        warning_label.setPixmap(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_MessageBoxWarning
        ).pixmap(32, 32))
        
        message = QLabel(
            f"Restore from backup '{backup_name}'?\n\n"
            "This will replace the current playlist content."
        )
        message.setWordWrap(True)
        
        self.content_layout.addWidget(warning_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.addWidget(message)
        
        # Update button text
        self.ok_btn.setText("Restore")

class SortConfirmDialog(BaseDialog):
    """Dialog for confirming playlist sorting."""
    
    def __init__(self, playlist_name: str, parent=None):
        super().__init__("Confirm Playlist Sort", parent)
        
        message = QLabel(
            f"Sort playlist '{playlist_name}'?\n\n"
            "This will reorder all entries. A backup will be created first."
        )
        message.setWordWrap(True)
        
        self.content_layout.addWidget(message)
        
        # Update button text
        self.ok_btn.setText("Sort")

class SafetyDialogs:
    """Factory class for creating safety dialogs."""
    
    @staticmethod
    def confirm_deletion(location: str, count: int) -> bool:
        """Show confirmation dialog for file deletion."""
        dialog = DeleteConfirmDialog(location, count, QApplication.activeWindow())
        return dialog.exec() == BaseDialog.DialogCode.Accepted

    @staticmethod
    def confirm_sync_operation(operation: str, count: int) -> bool:
        """Show confirmation dialog for sync operations."""
        dialog = SyncConfirmDialog(operation, count, QApplication.activeWindow())
        return dialog.exec() == BaseDialog.DialogCode.Accepted

    @staticmethod
    def show_backup_created(backup_path: Path):
        """Show notification of backup creation."""
        dialog = BackupCreatedDialog(backup_path, QApplication.activeWindow())
        dialog.exec()

    @staticmethod
    def confirm_bulk_operation(operation: str, count: int) -> bool:
        """Show confirmation dialog for bulk operations."""
        dialog = BulkOperationDialog(operation, count, QApplication.activeWindow())
        return dialog.exec() == BaseDialog.DialogCode.Accepted

    @staticmethod
    def confirm_restore_backup(backup_name: str) -> bool:
        """Show confirmation dialog for backup restoration."""
        dialog = RestoreBackupDialog(backup_name, QApplication.activeWindow())
        return dialog.exec() == BaseDialog.DialogCode.Accepted

    @staticmethod
    def confirm_sort_playlist(playlist_name: str) -> bool:
        """Show confirmation dialog for playlist sorting."""
        dialog = SortConfirmDialog(playlist_name, QApplication.activeWindow())
        return dialog.exec() == BaseDialog.DialogCode.Accepted
        
    @staticmethod
    def show_error(title: str, message: str):
        """Show error dialog."""
        dialog = ErrorDialog(title, message, QApplication.activeWindow())
        dialog.exec()