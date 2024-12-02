# core/services/ui_service.py

from pathlib import Path
from typing import Optional, Tuple, Any
from PyQt6.QtWidgets import (QWidget, QMessageBox, QFileDialog, 
                           QProgressDialog, QInputDialog)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
import logging

from core.services.service_base import ServiceProvider
from gui.dialogs.base_dialog import BaseDialog
from gui.dialogs.safety_dialogs import SafetyDialogs

class ProgressOperation:
    """Context manager for progress dialog operations."""
    
    def __init__(self, title: str, message: str, parent: Optional[QWidget] = None):
        self.progress = QProgressDialog(message, "Cancel", 0, 100, parent)
        self.progress.setWindowTitle(title)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.setAutoClose(True)
        self.progress.setAutoReset(True)
        
    def __enter__(self):
        self.progress.show()
        return self.progress
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.close()

class UIService(ServiceProvider):
    """Centralized service for common UI operations."""
    
    # Signals
    operation_cancelled = pyqtSignal(str)  # Operation identifier
    dialog_closed = pyqtSignal(str, object)  # Dialog identifier and result
    
    def __init__(self):
        super().__init__("ui_service")
        self.logger = logging.getLogger('ui_service')
        self._active_dialogs = []

    async def initialize(self) -> None:
        """Initialize the UI service."""
        self.logger.debug("Initializing UI service")
        # No specific initialization needed, but required by ServiceProvider
        pass

    async def start(self) -> None:
        """Start the UI service."""
        self.logger.debug("Starting UI service")
        # No specific start actions needed, but required by ServiceProvider
        pass

    async def stop(self) -> None:
        """Stop the UI service."""
        self.logger.debug("Stopping UI service")
        # Clean up any active dialogs
        self.cleanup()
        
    def confirm_operation(self, title: str, message: str, 
                         dangerous: bool = False) -> bool:
        """Show operation confirmation dialog."""
        try:
            return SafetyDialogs.confirm_operation(title, message, dangerous)
        except Exception as e:
            self.logger.error(f"Error showing confirmation dialog: {e}")
            return False
            
    def show_error(self, title: str, message: str):
        """Show error dialog."""
        try:
            SafetyDialogs.show_error(title, message)
        except Exception as e:
            self.logger.error(f"Error showing error dialog: {e}")
            
    def get_save_path(self, title: str, default_dir: str, 
                     file_filter: str) -> Optional[str]:
        """Show save file dialog."""
        try:
            path, _ = QFileDialog.getSaveFileName(
                None, title, default_dir, file_filter
            )
            return path if path else None
        except Exception as e:
            self.logger.error(f"Error showing save dialog: {e}")
            return None
            
    def get_open_path(self, title: str, default_dir: str,
                     file_filter: str) -> Optional[str]:
        """Show open file dialog."""
        try:
            path, _ = QFileDialog.getOpenFileName(
                None, title, default_dir, file_filter
            )
            return path if path else None
        except Exception as e:
            self.logger.error(f"Error showing open dialog: {e}")
            return None
            
    def get_directory(self, title: str, default_dir: str) -> Optional[str]:
        """Show directory selection dialog."""
        try:
            path = QFileDialog.getExistingDirectory(
                None, title, default_dir,
                QFileDialog.Option.ShowDirsOnly
            )
            return path if path else None
        except Exception as e:
            self.logger.error(f"Error showing directory dialog: {e}")
            return None
            
    def get_text_input(self, title: str, message: str, 
                      default: str = "") -> Optional[str]:
        """Show text input dialog."""
        try:
            text, ok = QInputDialog.getText(
                None, title, message,
                text=default
            )
            return text if ok else None
        except Exception as e:
            self.logger.error(f"Error showing input dialog: {e}")
            return None
            
    def show_progress_dialog(self, title: str, message: str,
                           parent: Optional[QWidget] = None) -> ProgressOperation:
        """Create progress dialog as context manager."""
        return ProgressOperation(title, message, parent)
            
    def show_backup_created(self, backup_path: Path):
        """Show backup creation notification."""
        try:
            SafetyDialogs.show_backup_created(backup_path)
        except Exception as e:
            self.logger.error(f"Error showing backup notification: {e}")
            
    def confirm_deletion(self, location: str, count: int) -> bool:
        """Show deletion confirmation dialog."""
        try:
            return SafetyDialogs.confirm_deletion(location, count)
        except Exception as e:
            self.logger.error(f"Error showing deletion confirmation: {e}")
            return False
            
    def confirm_sync(self, operation: str, count: int) -> bool:
        """Show sync confirmation dialog."""
        try:
            return SafetyDialogs.confirm_sync_operation(operation, count)
        except Exception as e:
            self.logger.error(f"Error showing sync confirmation: {e}")
            return False
            
    def show_custom_dialog(self, dialog: BaseDialog,
                          identifier: str) -> Any:
        """Show custom dialog and track result."""
        try:
            self._active_dialogs.append(dialog)
            result = dialog.exec()
            self._active_dialogs.remove(dialog)
            
            # Emit result
            self.dialog_closed.emit(identifier, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error showing custom dialog: {e}")
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
            return None
            
    def cleanup(self):
        """Clean up active dialogs."""
        try:
            # Close any active dialogs
            for dialog in self._active_dialogs[:]:
                try:
                    dialog.reject()
                    dialog.deleteLater()
                except Exception as e:
                    self.logger.error(f"Error closing dialog: {e}")
                    
            self._active_dialogs.clear()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")