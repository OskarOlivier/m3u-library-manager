# gui/windows/pages/sync/sync_page.py

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFrame
from PyQt6.QtCore import Qt, QTimer
from pathlib import Path
import logging

from app.config import Config
from gui.windows.pages.base_page import BasePage
from gui.components.panels.base_status_panel import StatusPanel
from .state import SyncPageState
from .handlers import ConnectionHandler, AnalysisHandler, SyncHandler
from .components import PlaylistPanel, SyncFilePanel

class SyncPage(BasePage):
    """Page for managing playlist synchronization."""
    def __init__(self, parent=None):
        self.logger = logging.getLogger('sync_page')
        
        # Initialize paths and state
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.music_dir = Path(Config.LOCAL_BASE)
        
        # Initialize state 
        self.state = SyncPageState()
        self.state.playlists_dir = self.playlists_dir  # Store for cache management
        
        # Initialize tracking flags
        self._ui_initialized = False
        self._handlers_initialized = False
        self._signals_connected = False
        
        # Initialize handlers as None first
        self.connection = None
        self.analysis_handler = None
        self.sync_handler = None
        
        super().__init__(parent)

    def init_page(self):
        """Initialize page components."""
        try:
            self.logger.debug("Initializing sync page components")
            
            if not self._handlers_initialized:
                self._init_handlers()

            if not self._ui_initialized:
                # Initialize panels
                self.playlist_panel = PlaylistPanel(
                    state=self.state,
                    on_analyze_all=self._handle_analyze_all,
                    on_upload=self._handle_upload_playlist
                )

                self.remote_panel = SyncFilePanel(
                    state=self.state,
                    title="Missing from Remote",
                    is_remote=True
                )
                
                self.local_panel = SyncFilePanel(
                    state=self.state,
                    title="Missing Locally",
                    is_remote=False
                )

                self.status_panel = StatusPanel(self.state)
                
                self._ui_initialized = True

            self.logger.debug("Sync page components initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing sync page: {e}", exc_info=True)
            raise

    def _init_handlers(self):
        """Initialize handlers safely."""
        try:
            self.logger.debug("Initializing handlers")
            self.connection = ConnectionHandler()
            self.analysis_handler = AnalysisHandler(self.state, self.connection)
            self.sync_handler = SyncHandler(self.state, self.connection)
            self._handlers_initialized = True
        except Exception as e:
            self.logger.error(f"Error initializing handlers: {e}")
            raise
        
    def setup_ui(self):
        """Set up the main UI layout."""
        if hasattr(self, '_layout'):
            self.logger.debug("UI already set up, skipping")
            return

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(12, 12, 12, 12)
        
        # Create main container
        main_container = QWidget(self)
        main_container.setStyleSheet("""
            QWidget {
                background-color: #202020;
            }
        """)
        self._layout.addWidget(main_container)
        
        # Panels layout
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(12)
        panels_layout.setContentsMargins(0, 0, 0, 0)

        # Create frames for each panel
        for panel in [self.playlist_panel, self.remote_panel, self.local_panel]:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #202020;
                    border: none;
                    border-radius: 4px;
                }
            """)
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(8, 8, 8, 8)
            frame_layout.addWidget(panel)
            panels_layout.addWidget(frame)
        
        # Main layout assembly
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addLayout(panels_layout)
        main_layout.addWidget(self.status_panel)

        # Connect signals if not already connected
        if not self._signals_connected:
            self.connect_signals()
            self._signals_connected = True
        
    def connect_signals(self):
        """Connect all panel signals."""
        try:
            # Playlist panel signals
            self.playlist_panel.selection_changed.connect(self._on_playlist_selected)
            self.playlist_panel.analyze_requested.connect(self._handle_analyze_playlist)
            
            # Sync operation signals
            self.remote_panel.sync_requested.connect(self._handle_sync_operation)
            self.local_panel.sync_requested.connect(self._handle_sync_operation)
            
            # Status signals
            self.state.sync_started.connect(self._on_sync_started)
            self.state.sync_completed.connect(self._on_sync_completed)
            self.state.error_occurred.connect(self._on_error)

            # Connect state signals for analysis updates
            self.state.analysis_completed.connect(self._on_analysis_completed)
            self.state.playlist_selected.connect(self._update_file_panels)

            self._signals_connected = True
            
        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}")

    def _handle_analyze_playlist(self, playlist_path: Path):
        """Handle single playlist analysis."""
        self.logger.debug(f"Starting analysis of playlist: {playlist_path}")
        if self.analysis_handler:
            self.analysis_handler.analyze_playlist(playlist_path)
            
    def _handle_analyze_all(self):
        """Handle analyze all button click."""
        self.logger.debug("Starting analysis of all playlists")
        if self.analysis_handler:
            self.analysis_handler.analyze_all_playlists(self.playlists_dir)
        
    def _handle_upload_playlist(self, playlist_path: Path):
        """Handle playlist upload request."""
        self.logger.debug(f"Uploading playlist: {playlist_path}")
        if self.sync_handler:
            self.sync_handler.upload_playlist(playlist_path)
        
    def _handle_sync_operation(self, operation: str, files: set[Path]):
        """Handle sync operation request."""
        self.logger.debug(f"Sync operation requested: {operation}")
        if self.sync_handler:
            self.sync_handler.sync_files(operation, files)
            
    def _on_playlist_selected(self, playlist_path: Path):
        """Handle playlist selection."""
        self.logger.debug(f"Playlist selected: {playlist_path}")
        
        # Update state
        self.state.set_current_playlist(playlist_path)
        
        # Update file panels with any existing analysis
        self._update_file_panels(playlist_path)
        
    def _update_file_panels(self, playlist_path: Path):
        """Update file panels with analysis results."""
        self.logger.debug(f"Updating file panels for {playlist_path.name}")
        
        # Clear current displays first
        self.remote_panel.clear_files()
        self.local_panel.clear_files()
        
        if playlist_path:
            # Update panels if analysis exists
            analysis = self.state.get_analysis(playlist_path)
            if analysis:
                self.logger.debug(f"Found analysis - Updating panels with "
                                f"{len(analysis.missing_remotely)} remote and "
                                f"{len(analysis.missing_locally)} local missing files")
                if analysis.missing_remotely:
                    self.remote_panel.add_files(analysis.missing_remotely)
                if analysis.missing_locally:
                    self.local_panel.add_files(analysis.missing_locally)
                    
    def _on_analysis_completed(self, playlist_path: Path, analysis):
        """Handle completed analysis."""
        self.logger.debug(f"Analysis completed for {playlist_path.name}")
        # The state will handle re-emitting selection if this is the current playlist
        # which will trigger _update_file_panels through the playlist_selected signal
                
    def _on_sync_started(self, operation: str):
        """Handle sync operation start."""
        self.logger.debug(f"Sync operation started: {operation}")
        
    def _on_sync_completed(self):
        """Handle sync operation completion."""
        self.logger.debug("Sync operation completed")
        
        # Refresh analysis for current playlist
        if self.state.current_playlist and self.analysis_handler:
            self.analysis_handler.analyze_playlist(self.state.current_playlist)
            
    def _on_error(self, error: str):
        """Handle error conditions."""
        self.logger.error(f"Error occurred: {error}")
                
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        try:
            # First initialize UI without connection
            if not self._ui_initialized:
                self.logger.debug("Initializing UI components")
                self.init_page()
                self.setup_ui()

            # Refresh playlists before connection check
            if hasattr(self, 'playlist_panel'):
                self.logger.debug("Refreshing playlists")
                self.playlist_panel.refresh_playlists(self.playlists_dir)

            # Schedule connection check after UI is visible
            QTimer.singleShot(100, self._check_connection)

        except Exception as e:
            self.logger.error(f"Error in show event: {e}", exc_info=True)

    def _check_connection(self):
        """Check SSH connection after UI is rendered."""
        if self.connection:
            self.logger.debug("Testing SSH connection")
            success, error = self.connection.get_connection()
            if not success:
                self.state.report_error(f"Connection failed: {error}")
                
    def hideEvent(self, event):
        """Handle hide event."""
        try:
            super().hideEvent(event)
            self.logger.debug("Hiding sync page")
        except Exception as e:
            self.logger.error(f"Error in hide event: {e}")
        
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Starting sync page cleanup")

            # Clean up handlers
            handlers = [
                ('analysis_handler', self.analysis_handler),
                ('sync_handler', self.sync_handler),
                ('connection', self.connection)
            ]
            
            for name, handler in handlers:
                if handler and hasattr(handler, 'cleanup'):
                    try:
                        self.logger.debug(f"Cleaning up {name}")
                        handler.cleanup()
                        setattr(self, name, None)
                    except Exception as e:
                        self.logger.error(f"Error cleaning up {name}: {e}")

            # Clean up panels
            panels = [
                ('playlist_panel', self.playlist_panel if hasattr(self, 'playlist_panel') else None),
                ('remote_panel', self.remote_panel if hasattr(self, 'remote_panel') else None),
                ('local_panel', self.local_panel if hasattr(self, 'local_panel') else None),
                ('status_panel', self.status_panel if hasattr(self, 'status_panel') else None)
            ]
            
            for name, panel in panels:
                if panel:
                    try:
                        self.logger.debug(f"Cleaning up {name}")
                        if hasattr(panel, 'cleanup'):
                            panel.cleanup()
                        panel.deleteLater()
                        setattr(self, name, None)
                    except Exception as e:
                        self.logger.error(f"Error cleaning up {name}: {e}")

            # Reset initialization flags
            self._ui_initialized = False
            self._handlers_initialized = False
            self._signals_connected = False

            # Remove layout
            if hasattr(self, '_layout'):
                QWidget().setLayout(self._layout)
                delattr(self, '_layout')

            # Call parent cleanup last
            super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during sync page cleanup: {e}", exc_info=True)