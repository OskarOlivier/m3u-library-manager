# gui/windows/pages/sync/components/sync_file_panel.py

from typing import Optional, Set
from pathlib import Path
import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

from gui.components.panels.base_file_panel import BaseFilePanel
from gui.dialogs.safety_dialogs import SafetyDialogs
from gui.components.styles.colors import (
    TEXT_COLOR,
    SUCCESS_COLOR,
    ERROR_COLOR,
    WARNING_COLOR,
    PRIMARY_ACCENT
)

class SyncFilePanel(BaseFilePanel):
    """Panel for handling sync operations in one direction."""
    
    sync_requested = pyqtSignal(str, object)  # operation_type, files
    operation_completed = pyqtSignal(bool)  # success status

    def __init__(self, state, title: str, is_remote: bool, parent: Optional[QWidget] = None):
        self.state = state
        self.is_remote = is_remote
        self.logger = logging.getLogger(f'sync_file_panel_{"remote" if is_remote else "local"}')
        
        # Initialize buttons before parent init
        self.add_button: Optional[QPushButton] = None
        self.delete_button: Optional[QPushButton] = None
        
        super().__init__(title=title, parent=parent)

    def setup_ui(self):
        """Set up the panel UI."""
        super().setup_ui()
        self.setup_action_buttons()

    def setup_action_buttons(self):
        """Set up sync-specific action buttons."""
        button_style = f"""
            QPushButton {{
                background-color: #2D2D2D;
                color: {TEXT_COLOR};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #404040;
            }}
            QPushButton:pressed {{
                background-color: #505050;
            }}
            QPushButton:disabled {{
                color: #999999;
                background-color: #2D2D2D;
            }}
        """

        # Create buttons based on panel type
        if self.is_remote:
            self.add_button = self._create_button(
                "Add to Remote",
                lambda: self._handle_sync_operation('add_remote')
            )
            self.delete_button = self._create_button(
                "Delete Locally",
                lambda: self._handle_sync_operation('delete_local')
            )
            self.logger.debug("Created remote operation buttons")
        else:
            self.add_button = self._create_button(
                "Add to Local",
                lambda: self._handle_sync_operation('add_local')
            )
            self.delete_button = self._create_button(
                "Delete from Remote",
                lambda: self._handle_sync_operation('delete_remote')
            )
            self.logger.debug("Created local operation buttons")
            
        # Add buttons to layout with styling
        for button in [self.add_button, self.delete_button]:
            button.setStyleSheet(button_style)
            self.action_layout.addWidget(button)
            
        self._update_button_states()
        self.logger.debug("Action buttons setup complete")

    def _handle_sync_operation(self, operation: str):
        """
        Handle sync operation with proper checks and confirmation.
        
        Args:
            operation: Type of sync operation to perform
        """
        try:
            self.logger.debug(f"Handling sync operation: {operation}")
            self.logger.debug(f"Current playlist: {self.state.current_playlist}")
            
            # Check if playlist is selected
            if not self.state.current_playlist:
                SafetyDialogs.show_error(
                    "No Playlist Selected",
                    "Please select a playlist before performing sync operations."
                )
                return
                
            files = self.get_checked_files()
            if not files:
                SafetyDialogs.show_error(
                    "No Files Selected",
                    "Please select files to process."
                )
                return

            # Show appropriate confirmation dialog
            if operation.startswith('delete'):
                location = 'local' if operation == 'delete_local' else 'remote'
                if not SafetyDialogs.confirm_deletion(location, len(files)):
                    self.logger.debug("Deletion cancelled by user")
                    return
            else:
                if not SafetyDialogs.confirm_sync_operation(operation, len(files)):
                    self.logger.debug("Sync cancelled by user")
                    return

            self.logger.info(f"Starting {operation} for {len(files)} files")
            self.logger.debug(f"Using playlist: {self.state.current_playlist}")
            self.sync_requested.emit(operation, files)
            self._disable_during_operation()

        except Exception as e:
            self.logger.error(f"Error handling sync operation: {e}", exc_info=True)
            SafetyDialogs.show_error(
                "Operation Error",
                f"An error occurred: {str(e)}"
            )

    def _disable_during_operation(self):
        """Disable panel during sync operation."""
        self.setEnabled(False)
        self.add_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.check_all_btn.setEnabled(False)
        self.uncheck_all_btn.setEnabled(False)

    def _enable_after_operation(self):
        """Re-enable panel after sync operation."""
        self.setEnabled(True)
        self._update_button_states()

    def start_sync(self, operation: str):
        """
        Start sync operation visual state.
        
        Args:
            operation: Type of operation being performed
        """
        self.logger.debug(f"Starting sync operation: {operation}")
        self._disable_during_operation()
        self.set_progress_visible(True)
        self.update_progress(0)

    def finish_sync(self, success: bool):
        """Complete sync operation visual state."""
        self.logger.debug(f"Finishing sync operation (success={success})")
        
        try:
            # Re-enable panel and all widgets
            self.setEnabled(True)
            
            # Re-enable all checkboxes and restore functionality
            for file_path, widget in self.file_widgets.items():
                widget.checkbox.setEnabled(True)
                widget.setEnabled(True)
                    
            # Re-enable scrolling
            self.file_list.setEnabled(True)
            
            # Update button states
            self._update_button_states()
            self.update_progress(100)
            
            # Hide progress bar after delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.set_progress_visible(False))
            
            self.operation_completed.emit(success)
            
        except Exception as e:
            self.logger.error(f"Error in finish_sync: {e}")

    def set_progress_visible(self, visible: bool):
        """Show or hide progress indication."""
        if hasattr(self, 'progress_widget'):
            self.progress_widget.setVisible(visible)

    def update_progress(self, value: int):
        """Update progress value."""
        if hasattr(self, 'progress_widget'):
            self.progress_widget.set_progress(value)

    def _update_button_states(self):
        """Update button enabled states based on selection."""
        has_checked = bool(self.get_checked_files())
        has_files = bool(self.file_widgets)
        has_playlist = self.state.current_playlist is not None
        
        if hasattr(self, 'add_button'):
            self.add_button.setEnabled(has_checked)
            
        if hasattr(self, 'delete_button'):
            # Local deletion always available if files exist
            if self.is_remote:
                self.delete_button.setEnabled(has_files)
            else:
                self.delete_button.setEnabled(has_checked)
        
        self.check_all_btn.setEnabled(has_files)
        self.uncheck_all_btn.setEnabled(has_checked)

    def set_error_state(self, file_paths: Set[Path]):
        """Mark specific files as having errors."""
        for path in file_paths:
            if path in self.file_widgets:
                widget = self.file_widgets[path]
                widget.set_error_state(True)

    def set_success_state(self, file_paths: Set[Path]):
        """Mark specific files as successfully processed."""
        for path in file_paths:
            if path in self.file_widgets:
                widget = self.file_widgets[path]
                widget.set_error_state(False)

    def set_warning_state(self, file_paths: Set[Path]):
        """Mark specific files with warnings."""
        for path in file_paths:
            if path in self.file_widgets:
                widget = self.file_widgets[path]
                # Use warning style if available
                widget.set_error_state(True)

    def reset_states(self):
        """Reset all file states to default."""
        for widget in self.file_widgets.values():
            widget.reset_state()

    def cleanup(self):
        """Clean up resources."""
        self.logger.debug("Cleaning up sync file panel")
        super().cleanup()