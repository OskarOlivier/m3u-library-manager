# gui/windows/pages/curation/curation_page.py

from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer

from app.config import Config
from gui.windows.pages.base_page import BasePage
from gui.components.panels.base_status_panel import StatusPanel
from core.matching.song_matcher import SongMatchResult
from core.matching.window_handler import WindowHandler, WindowTitleInfo
from core.playlist import PlaylistManager
from core.context import ApplicationContext, WindowService, PlaylistService
from .state import CurationState
from .handlers import SongHandler, PlaylistHandler, StatsHandler
from .components import PlaylistGrid, StatsPanel
from .components.song_selection_widget import SongSelectionWidget
from utils.m3u.parser import read_m3u, write_m3u

class CurationPage(BasePage):
    """Page for playlist curation and management."""
    
    def __init__(self, parent=None):
        # Initialize tracking flags first
        self._ui_initialized = False
        self._handlers_initialized = False
        self._signals_connected = False

        # Initialize core paths
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.music_dir = Path(Config.LOCAL_BASE)
        
        # Get application context
        self.context = ApplicationContext.get_instance()
        
        # Initialize state
        self.state = CurationState()
        self.state.playlists_dir = self.playlists_dir
        
        # Get services from context
        window_service = self.context.get_service(WindowService)
        playlist_service = self.context.get_service(PlaylistService)
        
        # Initialize with services from context
        self.window_handler = window_service.window_handler
        self.song_matcher = window_service.song_matcher
        self.playlist_manager = playlist_service.playlist_manager
        
        # Set playlist manager in state
        self.state.playlist_manager = self.playlist_manager
        
        # Initialize handlers with services
        self.song_handler = SongHandler(self.state, self.window_handler, self.song_matcher)
        self.playlist_handler = PlaylistHandler(self.state)
        
        self.logger = logging.getLogger('curation_page')
        self.logger.setLevel(logging.DEBUG)
        
        super().__init__(parent)  # This will call init_page() and setup_ui()

    def init_page(self):
        """Initialize page components."""
        try:
            self.logger.debug("Initializing curation page components")

            if not self._handlers_initialized:
                self._init_handlers()

            if not self._ui_initialized:
                from .components import PlaylistGrid, StatsPanel
                from .components.song_selection_widget import SongSelectionWidget

                # Initialize panels
                self.playlist_grid = PlaylistGrid(
                    state=self.state,
                    parent=self
                )

                self.song_selection = SongSelectionWidget()
                self.song_selection.setFixedHeight(40)
                self.song_selection.selection_changed.connect(self._on_file_selection_changed)

                # Initialize stats handler if needed
                if not hasattr(self, 'stats_handler'):
                    self.stats_handler = StatsHandler(self.state, self.playlists_dir)

                self._ui_initialized = True

            self.logger.debug("Page components initialized")

        except Exception as e:
            self.logger.error(f"Error initializing page: {e}", exc_info=True)
            self.context.ui_service.show_error("Initialization Error", str(e))
            raise
            
    def _init_handlers(self):
        """Initialize handlers safely."""
        try:
            self.logger.debug("Initializing handlers")
            if not hasattr(self, 'stats_handler') or self.stats_handler is None:
                self.stats_handler = StatsHandler(self.state, self.playlists_dir)
            self._handlers_initialized = True
        except Exception as e:
            self.logger.error(f"Error initializing handlers: {e}")
            self.context.ui_service.show_error("Handler Initialization Error", str(e))
            raise
        
    def setup_ui(self):
        """Set up the main UI layout."""
        # If layout already exists, skip setup
        if hasattr(self, '_layout'):
            self.logger.debug("UI already set up, skipping")
            return

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(12, 12, 12, 12)
        
        # Create main container
        main_container = QWidget(self)
        main_container.setStyleSheet("background-color: #202020;")
        self._layout.addWidget(main_container)
        
        # Main container layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Song selection at top (fixed height)
        if not hasattr(self, 'song_selection'):
            self.song_selection = SongSelectionWidget()
            self.song_selection.setFixedHeight(40)
            self.song_selection.selection_changed.connect(self._on_file_selection_changed)
        main_layout.addWidget(self.song_selection)
        
        # Playlist grid (takes remaining space)
        if not hasattr(self, 'playlist_grid'):
            self.playlist_grid = PlaylistGrid(self.state)
            self.playlist_grid.setSizePolicy(
                QSizePolicy.Policy.Expanding, 
                QSizePolicy.Policy.Expanding
            )
        main_layout.addWidget(self.playlist_grid)
        
        # Bottom container for status and stats
        bottom_container = QWidget()
        bottom_container.setFixedHeight(50)
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        
        # Status panel (left side)
        if not hasattr(self, 'status_panel'):
            self.status_panel = StatusPanel(self.state)
        self.status_panel.setFixedHeight(40)
        bottom_layout.addWidget(self.status_panel)
        
        # Stats panel (right side)
        if not hasattr(self, 'stats_panel'):
            self.stats_panel = StatsPanel(self.state)
        self.stats_panel.setFixedHeight(40)
        bottom_layout.addWidget(self.stats_panel)
        
        main_layout.addWidget(bottom_container)

        # Connect signals if not already connected
        if not hasattr(self, '_signals_connected') or not self._signals_connected:
            self.connect_signals()
            self._signals_connected = True
        
    def connect_signals(self):
        """Connect all component signals."""
        try:
            self.logger.debug("Connecting signals")
            
            # Set debug logging for all components
            loggers = [
                'playlist_handler',
                'playlist_manager',
                'playlist_grid',
                'song_handler',
                'stats_handler'
            ]
            for logger_name in loggers:
                logging.getLogger(logger_name).setLevel(logging.DEBUG)
            
            # Connect playlist signals
            if hasattr(self, 'playlist_grid'):
                self.playlist_grid.playlist_clicked.connect(self._on_playlist_clicked)
                self.playlist_grid.playlist_toggled.connect(self._on_playlist_toggled)
                self.playlist_grid.selection_changed.connect(self._on_selection_changed)
            
            # Connect state signals
            if hasattr(self, 'state'):
                self.state.song_changed.connect(self._on_song_changed)
                self.state.song_cleared.connect(self._on_song_cleared)
                self.state.file_selection_changed.connect(self._on_file_selection_changed)
                self.state.error_occurred.connect(self._on_error)
            
            # Connect song selection signals
            if hasattr(self, 'song_selection'):
                self.song_selection.selection_changed.connect(self._handle_selection_change)

            self.logger.debug("Signals connected")

        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}", exc_info=True)
            self.context.ui_service.show_error("Signal Connection Error", str(e))
        
    def _on_playlist_clicked(self, playlist_path: Path):
        """Handle playlist click."""
        self.logger.debug(f"Playlist clicked: {playlist_path}")
        if not self.state.current_song or not self.state.current_file:
            return
            
        # Let playlist handler handle the toggle
        self.playlist_handler.toggle_song_in_playlist(playlist_path)
        
    def _on_playlist_toggled(self, playlist_path: Path, selected: bool):
        """Handle playlist toggle state change."""
        self.logger.debug(f"Playlist toggled: {playlist_path} -> {selected}")
        if selected:
            self.state.add_playlist_selection(playlist_path)
        else:
            self.state.remove_playlist_selection(playlist_path)
            
    def _on_selection_changed(self):
        """Handle general selection state changes."""
        self.logger.debug("Selection state changed")
        
    def _on_song_changed(self, song_match: SongMatchResult):
        """Handle song change with match results."""
        self.logger.debug(f"Song changed: {song_match.artist} - {song_match.title}")
        self.song_selection.update_song(song_match)
        
    def _on_song_cleared(self):
        """Handle song stopped."""
        self.song_selection.clear_song()
        self.state.clear_playlist_selections()
            
    def _on_file_selection_changed(self, file_path: Path):
        """Handle user selecting different file match."""
        self.logger.debug(f"File selection changed to: {file_path}")
        
        # Update song handler
        self.song_handler.update_filepath_selection(file_path)
        
    def _on_error(self, error: str):
        """Handle error events from state."""
        self.context.ui_service.show_error("Operation Error", error)

    def _handle_selection_change(self, file_path: Path):
        """Handle selection changes from the song selection widget."""
        self.state.set_current_file(file_path)

    def refresh_playlists(self):
        """Refresh playlist grid and stats."""
        if hasattr(self, 'playlist_grid'):
            self.playlist_grid.refresh_playlists(self.playlists_dir)
            
    def calculate_stats(self):
        """Start playlist stats calculation."""
        if hasattr(self, 'stats_handler'):
            self.stats_handler.start_analysis()

    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        try:
            # Only initialize if needed
            if not self._ui_initialized:
                self.logger.debug("Initializing UI components")
                self.init_page()
                self.setup_ui()

            self.logger.debug("Starting song detection")
            if self.song_handler:
                self.song_handler.start()
            
            # Refresh playlists
            if hasattr(self, 'playlist_grid'):
                self.logger.debug("Refreshing playlists")
                self.refresh_playlists()
                self.calculate_stats()
            
            # If no new song detected after a short delay, restore cached state
            def check_restore():
                if not self.state.current_song:
                    self.logger.debug("No new song detected, attempting to restore cached state")
                    if self.state.restore_cached_state():
                        self.logger.debug("Successfully restored cached state")
                    else:
                        self.logger.debug("No cached state to restore")
            
            # Check after 1 second delay
            QTimer.singleShot(1000, check_restore)

        except Exception as e:
            self.logger.error(f"Error in show event: {e}", exc_info=True)
            self.context.ui_service.show_error("Show Event Error", str(e))

    def hideEvent(self, event):
        """Handle hide event."""
        try:
            super().hideEvent(event)
            self.logger.debug("Hiding curation page")
            
            if self.song_handler:
                self.song_handler.stop()
                
            if hasattr(self, 'state'):
                self.state.cache_current_state()
                
        except Exception as e:
            self.logger.error(f"Error in hide event: {e}")
            self.context.ui_service.show_error("Hide Event Error", str(e))
                
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Starting curation page cleanup")

            # Clean up handlers
            if hasattr(self, 'song_handler'):
                self.logger.debug("Cleaning up song handler")
                self.song_handler.cleanup()

            if hasattr(self, 'stats_handler'):
                self.logger.debug("Cleaning up stats handler")
                self.stats_handler.cleanup()

            # Clean up UI components
            for component in ['song_selection', 'playlist_grid', 'status_panel', 'stats_panel']:
                if hasattr(self, component):
                    widget = getattr(self, component)
                    if widget and hasattr(widget, 'cleanup'):
                        self.logger.debug(f"Cleaning up {component}")
                        widget.cleanup()
                    if widget:
                        widget.deleteLater()
                    setattr(self, component, None)

            # Remove layout if it exists
            if hasattr(self, '_layout'):
                QWidget().setLayout(self._layout)
                delattr(self, '_layout')

            # Reset initialization flags
            self._ui_initialized = False
            self._handlers_initialized = False
            self._signals_connected = False

            # Call parent cleanup last
            super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)
            self.context.ui_service.show_error("Cleanup Error", str(e))