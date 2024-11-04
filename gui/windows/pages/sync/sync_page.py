# gui/windows/pages/sync/sync_page.py

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFrame
from PyQt6.QtCore import Qt
from pathlib import Path
import logging

from app.config import Config
from gui.windows.pages import BasePage
from .components import PlaylistPanel, FileListPanel, StatusPanel
from .state import SyncPageState
from .handlers import ConnectionHandler, AnalysisHandler, SyncHandler

class SyncPage(BasePage):
    """Main sync page that coordinates between components."""
    
    def __init__(self):
        # Initialize state and handlers first
        self.state = SyncPageState()
        self.connection = ConnectionHandler()
        self.analysis_handler = AnalysisHandler(self.state, self.connection)
        self.sync_handler = SyncHandler(self.state, self.connection)
        super().__init__()
        
    def setup_ui(self):
        """Set up the main UI layout."""
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Create main container
        main_container = QWidget(self)
        main_container.setStyleSheet("""
            QWidget {
                background-color: #202020;
            }
        """)
        layout.addWidget(main_container)
        
        # Create panels layout
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(12)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        
        # Initialize panels
        self.playlist_panel = PlaylistPanel(
            self.state,
            on_analyze=self.analysis_handler.analyze_playlist,
            on_analyze_all=lambda: self.analysis_handler.analyze_all_playlists(Path(Config.PLAYLISTS_DIR))
        )
        
        self.file_list_panel = FileListPanel(
            self.state,
            on_sync=self.sync_handler.sync_files
        )
        
        self.status_panel = StatusPanel(self.state)
        
        # Create and style panel frames
        for panel in [self.playlist_panel, 
                     self.file_list_panel.remote_panel,
                     self.file_list_panel.local_panel]:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #202020;
                    border: none;
                    border-radius: 2px;
                }
            """)
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(8, 8, 8, 8)
            frame_layout.addWidget(panel)
            panels_layout.addWidget(frame)
        
        # Add panels and status to main layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addLayout(panels_layout)
        main_layout.addWidget(self.status_panel)
        
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Refresh playlists when page is shown
        if hasattr(self, 'playlist_panel'):
            self.playlist_panel.refresh_playlists()
            
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # Clear selection when page is hidden
        if hasattr(self, 'state'):
            self.state.set_current_playlist(None)
            
    def cleanup(self):
        """Clean up handlers and resources."""
        if hasattr(self, 'analysis_handler'):
            self.analysis_handler.cleanup()
        if hasattr(self, 'sync_handler'):
            self.sync_handler.cleanup()
        if hasattr(self, 'connection'):
            self.connection.cleanup()