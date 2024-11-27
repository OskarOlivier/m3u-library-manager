# gui/windows/pages/maintenance/maintenance_page.py

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFrame
from PyQt6.QtCore import Qt
from pathlib import Path
import logging

from app.config import Config
from gui.windows.pages.base_page import BasePage
from gui.components.panels.base_status_panel import StatusPanel
from .state import MaintenanceState
from .handlers import DeleteHandler, RepairHandler, AnalysisHandler
from core.playlist import PlaylistManager

class MaintenancePage(BasePage):
    """Page for managing playlist health and organization."""
    
    def __init__(self):
        # Initialize state
        self.state = MaintenanceState()
        
        # Initialize paths
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        
        # Initialize tracking flags
        self._ui_initialized = False
        self._handlers_initialized = False
        self._signals_connected = False
        
        # Initialize handlers as None first
        self.delete_handler = None
        self.repair_handler = None
        self.analysis_handler = None
        
        # Initialize playlist manager
        self.playlist_manager = PlaylistManager(
            Path(Config.LOCAL_BASE),
            Path(Config.PLAYLISTS_DIR),
            Path(Config.BACKUP_DIR)
        )
        
        self.logger = logging.getLogger('maintenance_page')
        super().__init__()

    def init_page(self):
        """Initialize page components."""
        try:
            self.logger.debug("Initializing maintenance page components")
            
            if not self._handlers_initialized:
                self._init_handlers()

            if not self._ui_initialized:
                from .components import PlaylistPanel, FileLocatorPanel, SortPanel
                
                # Initialize panels
                self.playlist_panel = PlaylistPanel(state=self.state)
                self.file_locator_panel = FileLocatorPanel(state=self.state)
                self.sort_panel = SortPanel(state=self.state)
                self.status_panel = StatusPanel(self.state)
                
                self._ui_initialized = True
                
            self.logger.debug("Maintenance page components initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing maintenance page: {e}", exc_info=True)
            raise

    def _init_handlers(self):
        """Initialize handlers safely."""
        try:
            self.logger.debug("Initializing handlers")
            self.delete_handler = DeleteHandler()
            self.repair_handler = RepairHandler()
            self.analysis_handler = AnalysisHandler(self.state)
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
        
        # Create and style panel frames with 2:2:1 ratio
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(12)
        panels_layout.setContentsMargins(0, 0, 0, 0)

        # Create frames for each panel
        def create_panel_frame(panel, stretch):
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
            panels_layout.addWidget(frame, stretch)
            return frame

        # Add panels with specified ratio (2:2:1)
        create_panel_frame(self.playlist_panel, 2)
        create_panel_frame(self.file_locator_panel, 2)
        create_panel_frame(self.sort_panel, 1)

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
            # Connect playlist panel signals
            if hasattr(self, 'playlist_panel'):
                self.playlist_panel.delete_requested.connect(
                    lambda p: self.delete_handler.delete_playlist(p) if self.delete_handler else None
                )
                self.playlist_panel.repair_requested.connect(
                    lambda p: self.repair_handler.repair_playlist(p) if self.repair_handler else None
                )
                self.playlist_panel.analyze_requested.connect(
                    lambda p: self.analysis_handler.analyze_playlist(p) if self.analysis_handler else None
                )

            self._signals_connected = True
            
        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}")
            
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        try:
            # Only initialize if needed
            if not self._ui_initialized:
                self.logger.debug("Initializing UI components")
                self.init_page()
                self.setup_ui()

            # Ensure handlers are initialized
            if not self._handlers_initialized:
                self._init_handlers()

            # Update UI if initialized
            if hasattr(self, 'playlist_panel') and self.playlist_panel:
                self.logger.debug("Updating playlist panel")
                self.playlist_panel.refresh_playlists(self.playlists_dir)

            # Clear selection when showing page
            if hasattr(self, 'state'):
                self.logger.debug("Clearing selection state")
                self.state.set_current_playlist(None)

        except Exception as e:
            self.logger.error(f"Error in show event: {e}", exc_info=True)
            
    def hideEvent(self, event):
        """Handle hide event."""
        try:
            super().hideEvent(event)
            self.logger.debug("Hiding maintenance page")
            # Clear selection when page is hidden
            if hasattr(self, 'state'):
                self.state.set_current_playlist(None)
        except Exception as e:
            self.logger.error(f"Error in hide event: {e}")
                    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Starting maintenance page cleanup")

            # Clean up handlers
            handlers = [
                ('delete_handler', self.delete_handler),
                ('repair_handler', self.repair_handler),
                ('analysis_handler', self.analysis_handler)
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
                ('file_locator_panel', self.file_locator_panel if hasattr(self, 'file_locator_panel') else None),
                ('sort_panel', self.sort_panel if hasattr(self, 'sort_panel') else None),
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
            self.logger.error(f"Error during maintenance page cleanup: {e}", exc_info=True)