# gui/windows/pages/curation/curation_page.py
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from pathlib import Path
import logging

from app.config import Config
from gui.windows.pages.base import BasePage
from gui.components.status_panel import StatusPanel
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
        
        super().__init__(parent)
        
    def setup_ui(self):
        """Set up the curation page UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Create main container
        main_container = QWidget()
        main_container.setStyleSheet("background-color: #202020;")
        layout.addWidget(main_container)
        
        # Main container layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Song info at top
        self.song_info = SongInfoPanel(self.state)
        main_layout.addWidget(self.song_info)
        
        # Playlist grid (takes most space)
        self.playlist_grid = PlaylistGrid(self.state)
        main_layout.addWidget(self.playlist_grid)
        
        # Bottom container for status and stats
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(12)
        
        # Status panel (left side)
        self.status_panel = StatusPanel(self.state)
        bottom_layout.addWidget(self.status_panel)
        
        # Stats panel (right side)
        self.stats_panel = StatsPanel(self.state)
        bottom_layout.addWidget(self.stats_panel)
        
        main_layout.addWidget(bottom_container)
        
        # Connect signals
        self.state.playlist_clicked.connect(self.playlist_handler.toggle_song_in_playlist)
        
        # Initial playlist load
        self.refresh_playlists()
        
        # Start song detection
        self.song_handler.start()
        
        from .handlers.stats_handler import StatsHandler
        self.stats_handler = StatsHandler(self.state, self.playlists_dir)
        
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        if hasattr(self, 'song_handler'):
            self.song_handler.start()
        if hasattr(self, 'playlist_grid'):
            self.refresh_playlists()
            self.calculate_stats()

    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        if hasattr(self, 'song_handler'):
            self.song_handler.stop()
        if hasattr(self, 'state'):
            self.state.clear_current_song()

    def calculate_stats(self):
        """Start playlist stats calculation."""
        if hasattr(self, 'stats_handler'):
            self.stats_handler.start_analysis()
            
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