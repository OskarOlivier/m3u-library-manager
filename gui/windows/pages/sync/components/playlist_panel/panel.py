# gui/windows/pages/sync/components/playlist_panel/panel.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Callable, Optional
import logging

from ...state import SyncPageState
from .playlist_list import PlaylistList
from .button_panel import ButtonPanel
from .header import PanelHeader

class PlaylistPanel(QWidget):
    """Main playlist panel combining subcomponents."""
    
    def __init__(self, 
                 state: SyncPageState, 
                 on_analyze_all: Callable[[], None],
                 on_upload: Callable[[Path], None],
                 parent: Optional[QWidget] = None):
        """Initialize PlaylistPanel.
        
        Args:
            state: Application state manager
            on_analyze_all: Callback for analyze all action
            on_upload: Callback for upload action
            parent: Parent widget
        """
        super().__init__(parent)
        self.state = state
        self.logger = logging.getLogger('playlist_panel')
        
        # Create subcomponents
        self.header = PanelHeader()
        self.playlist_list = PlaylistList(state)
        self.button_panel = ButtonPanel(
            state=state,
            on_analyze_all=on_analyze_all,
            on_upload=on_upload
        )
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the panel layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self.header)
        layout.addWidget(self.playlist_list)
        layout.addWidget(self.button_panel)
        
    def connect_signals(self):
        """Connect internal signals between components."""
        self.playlist_list.selection_changed.connect(self.button_panel.on_selection_changed)
        self.playlist_list.count_changed.connect(self.header.update_count)
        
        # Connect to state signals
        self.state.analysis_completed.connect(self.playlist_list.on_analysis_completed)
        self.state.analysis_all_completed.connect(self.button_panel.on_analysis_all_completed)
        self.state.sync_started.connect(self.button_panel.on_sync_started)
        self.state.sync_completed.connect(self.button_panel.on_sync_completed)
        
    def refresh_playlists(self):
        """Refresh playlist display."""
        self.playlist_list.refresh_playlists()
        
    def cleanup(self):
        """Clean up resources."""
        self.playlist_list.cleanup()