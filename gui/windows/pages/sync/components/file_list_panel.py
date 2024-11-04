# gui/windows/pages/sync/components/file_list_panel.py

"""File list panels implementation."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Callable, Set, Optional

from ..state import SyncPageState, PlaylistAnalysis
from gui.widgets.sync_widgets import FileListWidget

class FilePanel(QWidget):
    """Base panel for file lists."""
    
    def __init__(self, title: str, state: SyncPageState):
        super().__init__()
        self.state = state
        self.title = title
        self.count = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Set up panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title and count
        header = QHBoxLayout()
        
        # Title label
        title = QLabel(self.title)
        title.setFont(QFont("Segoe UI", 11))
        title.setStyleSheet("color: white;")
        header.addWidget(title)
        
        # Count label
        self.count_label = QLabel()
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: #999999;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.count_label)
        
        layout.addLayout(header)
        
        # File list
        self.file_list = FileListWidget()
        layout.addWidget(self.file_list)
        
        # Button container
        self.button_container = QVBoxLayout()
        layout.addLayout(self.button_container)
        
        # Selection buttons
        check_buttons = QHBoxLayout()
        self.check_all_btn = QPushButton("Check All")
        self.uncheck_all_btn = QPushButton("Uncheck All")
        
        self.check_all_btn.clicked.connect(lambda: self.file_list.set_all_checked(True))
        self.uncheck_all_btn.clicked.connect(lambda: self.file_list.set_all_checked(False))
        
        check_buttons.addWidget(self.check_all_btn)
        check_buttons.addWidget(self.uncheck_all_btn)
        self.button_container.addLayout(check_buttons)
        
        # Apply button style
        button_style = """
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                color: #666666;
            }
        """
        for button in [self.check_all_btn, self.uncheck_all_btn]:
            button.setStyleSheet(button_style)
            
    def update_count(self, count: int):
        """Update the file count display."""
        self.count = count
        self.count_label.setText(f"{count} files")
        
    def clear(self):
        """Clear the file list."""
        self.file_list.clear()
        self.update_count(0)
        
    def add_files(self, files: Set[Path]):
        """Add files to the list."""
        self.clear()
        for file_path in sorted(files):
            self.file_list.add_file_item(file_path)
        self.update_count(len(files))

class RemotePanel(FilePanel):
    """Panel for files missing remotely."""
    
    def __init__(self, state: SyncPageState, on_sync: Callable[[str, Set[Path]], None]):
        super().__init__("Missing Remotely", state)
        self.on_sync = on_sync
        self.setup_action_buttons()
        
    def setup_action_buttons(self):
        """Add remote-specific action buttons."""
        action_buttons = QHBoxLayout()
        
        self.add_remote_btn = QPushButton("Add to Remote")
        self.add_remote_btn.clicked.connect(self.on_add_remote)
        
        self.delete_local_btn = QPushButton("Delete from Local")
        self.delete_local_btn.clicked.connect(self.on_delete_local)
        
        action_buttons.addWidget(self.add_remote_btn)
        action_buttons.addWidget(self.delete_local_btn)
        
        # Add to button container before check buttons
        self.button_container.insertLayout(0, action_buttons)
        
        # Style buttons
        for button in [self.add_remote_btn, self.delete_local_btn]:
            button.setStyleSheet(self.check_all_btn.styleSheet())
            button.setEnabled(False)
            
    def on_add_remote(self):
        """Handle add to remote action."""
        files = self.file_list.get_checked_files()
        if files:
            self.on_sync('add_remote', files)
            
    def on_delete_local(self):
        """Handle delete from local action."""
        files = self.file_list.get_checked_files()
        if files:
            self.on_sync('delete_local', files)

class LocalPanel(FilePanel):
    """Panel for files missing locally."""
    
    def __init__(self, state: SyncPageState, on_sync: Callable[[str, Set[Path]], None]):
        super().__init__("Missing Locally", state)
        self.on_sync = on_sync
        self.setup_action_buttons()
        
    def setup_action_buttons(self):
        """Add local-specific action buttons."""
        action_buttons = QHBoxLayout()
        
        self.add_local_btn = QPushButton("Add to Local")
        self.add_local_btn.clicked.connect(self.on_add_local)
        
        self.delete_remote_btn = QPushButton("Delete from Remote")
        self.delete_remote_btn.clicked.connect(self.on_delete_remote)
        
        action_buttons.addWidget(self.add_local_btn)
        action_buttons.addWidget(self.delete_remote_btn)
        
        # Add to button container before check buttons
        self.button_container.insertLayout(0, action_buttons)
        
        # Style buttons
        for button in [self.add_local_btn, self.delete_remote_btn]:
            button.setStyleSheet(self.check_all_btn.styleSheet())
            button.setEnabled(False)
            
    def on_add_local(self):
        """Handle add to local action."""
        files = self.file_list.get_checked_files()
        if files:
            self.on_sync('add_local', files)
            
    def on_delete_remote(self):
        """Handle delete from remote action."""
        files = self.file_list.get_checked_files()
        if files:
            self.on_sync('delete_remote', files)

class FileListPanel:
    """Manages both remote and local file list panels."""
    
    def __init__(self, state: SyncPageState, 
                 on_sync: Callable[[str, Set[Path]], None]):
        self.state = state
        self.on_sync = on_sync
        
        # Create panels
        self.remote_panel = RemotePanel(state, on_sync)
        self.local_panel = LocalPanel(state, on_sync)
        
        # Connect state signals
        self.connect_signals()
        
    def connect_signals(self):
        """Connect to state signals."""
        # Clear panels when playlist is deselected
        self.state.playlist_deselected.connect(self.clear_panels)
        
        # Update panels when analysis completes
        self.state.analysis_completed.connect(self.on_analysis_completed)
        
        # Enable/disable buttons during sync
        self.state.sync_started.connect(lambda _: self.set_buttons_enabled(False))
        self.state.sync_completed.connect(lambda: self.set_buttons_enabled(True))
        
    def clear_panels(self):
        """Clear both panels."""
        self.remote_panel.clear()
        self.local_panel.clear()
        self.set_buttons_enabled(False)
        
    def set_buttons_enabled(self, enabled: bool):
        """Enable or disable all action buttons."""
        for button in [
            self.remote_panel.add_remote_btn,
            self.remote_panel.delete_local_btn,
            self.local_panel.add_local_btn,
            self.local_panel.delete_remote_btn
        ]:
            button.setEnabled(enabled)
            
    def on_analysis_completed(self, playlist_path: Path, analysis: PlaylistAnalysis):
        """Handle completed analysis."""
        if playlist_path == self.state.current_playlist:
            # Update remote panel
            self.remote_panel.add_files(analysis.missing_remotely)
            
            # Update local panel
            self.local_panel.add_files(analysis.missing_locally)
            
            # Enable buttons if there are differences
            self.set_buttons_enabled(analysis.has_differences)