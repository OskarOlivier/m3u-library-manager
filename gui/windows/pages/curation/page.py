# gui/windows/pages/curation/page.py

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from pathlib import Path
import logging

from app.config import Config
from gui.windows.pages.base import BasePage
from core.matching.window_handler import WindowHandler
from core.playlist import PlaylistManager

from .state import CurationState
from .handlers import SongHandler, PlaylistHandler 
from .components import PlaylistGrid, SongInfoPanel, StatsPanel

class CurationPage(BasePage):
    """Page for playlist curation and management."""
    
    def __init__(self, parent=None):
        # Initialize paths and managers first
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.music_dir = Path(Config.LOCAL_BASE)
        
        # Initialize state
        self.state = CurationState()
        self.state.playlists_dir = self.playlists_dir
        
        # Initialize playlist manager
        self.playlist_manager = PlaylistManager(
            self.music_dir,
            self.playlists_dir,
            Path(Config.BACKUP_DIR)
        )
        self.state.playlist_manager = self.playlist_manager
        
        # Initialize handlers
        self.song_handler = SongHandler(self.state)
        self.playlist_handler = PlaylistHandler(self.state)
        
        self.logger = logging.getLogger('curation_page')
        
        # Call parent class __init__
        super().__init__(parent)
        
    def setup_ui(self):
        """Set up the curation page UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Status and stats container
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(16)
        
        # Song info panel (fixed width)
        self.song_info = SongInfoPanel(self.state)
        status_layout.addWidget(self.song_info)
        
        # Stats panel (right aligned)
        self.stats_panel = StatsPanel(self.state)
        status_layout.addWidget(self.stats_panel)
        
        layout.addWidget(status_container)
        
        # Playlist grid
        self.playlist_grid = PlaylistGrid(self.state)
        
        # Connect signals
        self.state.playlist_clicked.connect(self.playlist_handler.toggle_song_in_playlist)
        
        layout.addWidget(self.playlist_grid)
        
        # Initial playlist load
        self.refresh_playlists()
        
        # Start song detection
        self.song_handler.start()
        
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Refresh playlists when page is shown
        if hasattr(self, 'playlist_grid'):
            self.refresh_playlists()
        
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # Clear current song when page is hidden
        if hasattr(self, 'state'):
            self.state.clear_current_song()
            
    def refresh_playlists(self):
        """Refresh playlist grid and stats."""
        if hasattr(self, 'playlist_grid'):
            self.playlist_grid.refresh_playlists(self.playlists_dir)
            
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'song_handler'):
            self.song_handler.cleanup()
        if hasattr(self, 'playlist_handler'):
            self.playlist_handler.cleanup()