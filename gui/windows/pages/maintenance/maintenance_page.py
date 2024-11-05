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
            on_analyze=self.file_locator.analyze_playlist,
            on_delete=self.delete_handler.delete_playlist
        )
        
        self.file_locator_panel = FileLocatorPanel(
            self.state,
            on_locate=self.file_locator.locate_files
        )
        
        self.sort_panel = SortPanel(
            self.state,
            on_sort=self.sort_handler.sort_playlist
        )
        
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
        """Clean up resources."""
        if hasattr(self, 'file_locator'):
            self.file_locator.cleanup()
        if hasattr(self, 'sort_handler'):
            self.sort_handler.cleanup()
        if hasattr(self, 'delete_handler'):
            self.delete_handler.cleanup()