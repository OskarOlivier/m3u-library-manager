# gui/windows/pages/maintenance/maintenance_page.py

"""Maintenance page implementation."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFrame
from PyQt6.QtCore import Qt
from pathlib import Path
import logging

from gui.windows.pages import BasePage
from .components import (
    PlaylistPanel, 
    FileLocatorPanel, 
    SortPanel,
    StatusPanel
)
from .state import MaintenanceState
from .handlers import (
    FileLocatorHandler,
    SortHandler,
    DeleteHandler
)

class MaintenancePage(BasePage):
    """Maintenance page for managing playlists and locating missing files."""
    
    def __init__(self):
        # Initialize state and handlers first
        self.state = MaintenanceState()
        self.file_locator = FileLocatorHandler(self.state)
        self.sort_handler = SortHandler(self.state)
        self.delete_handler = DeleteHandler(self.state)
        self.logger = logging.getLogger('maintenance_page')
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
        self.playlist_panel = PlaylistPanel(self.state)
        # Connect panel signals
        self.playlist_panel.playlistAnalyzed.connect(self.file_locator.analyze_playlist)
        self.playlist_panel.playlistDeleted.connect(self.delete_handler.delete_playlist)
        
        self.file_locator_panel = FileLocatorPanel(self.state)
        self.file_locator_panel.filesLocated.connect(self.file_locator.locate_files)
        
        self.sort_panel = SortPanel(self.state)
        
        self.status_panel = StatusPanel(self.state)
        
        # Create and style panel frames
        for panel in [
            self.playlist_panel,
            self.file_locator_panel,
            self.sort_panel
        ]:
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
        
        # Connect state signals
        self.connect_signals()
        
    def connect_signals(self):
        """Connect all state signals."""
        # Analysis state
        self.state.analysis_started.connect(
            lambda p: self.state.set_status(f"Analyzing {p.name}..."))
        self.state.analysis_completed.connect(
            lambda p, _: self.state.set_status(f"Analysis complete for {p.name}"))
        self.state.analysis_all_started.connect(
            lambda: self.state.set_status("Analyzing all playlists..."))
        self.state.analysis_all_completed.connect(
            lambda: self.state.set_status("All playlists analyzed"))
        
        # Operation state
        self.state.operation_started.connect(
            lambda op: self.state.set_status(f"Running {op}..."))
        self.state.operation_completed.connect(
            lambda op, success: self.state.set_status(
                f"{op} {'completed successfully' if success else 'failed'}"))
            
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Refresh playlists when page is shown
        if hasattr(self, 'playlist_panel'):
            from app.config import Config
            self.playlist_panel.refresh_playlists(Path(Config.PLAYLISTS_DIR))
            
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # Clear selection when page is hidden
        if hasattr(self, 'state'):
            self.state.set_current_playlist(None)
            
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'file_locator'):
            self.file_locator.cleanup()
        if hasattr(self, 'sort_handler'):
            self.sort_handler.cleanup()
        if hasattr(self, 'delete_handler'):
            self.delete_handler.cleanup()