# gui/windows/pages/proximity/proximity_page.py

from pathlib import Path
import logging
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QFrame, QLabel, QProgressBar
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import tempfile
import codecs
import json

from app.config import Config
from gui.windows.pages.base_page import BasePage
from core.context import ApplicationContext
from .state import ProximityState
from .handlers.visualization_handler import VisualizationHandler
from gui.components.panels.base_status_panel import StatusPanel

class ProximityPage(BasePage):
    """Page for visualizing playlist relationships."""
    
    initialization_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        # Initialize logger first
        self.logger = logging.getLogger('proximity_page')
        
        # Initialize paths and context
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.context = ApplicationContext.get_instance()
        
        # Initialize state
        self.state = ProximityState()
        
        # Initialize tracking flags
        self._ui_initialized = False
        self._handlers_initialized = False
        self._signals_connected = False
        self._cache_initialized = False
        self._is_first_show = True
        
        super().__init__(parent)
        
        # Connect to cache initialization
        self.context.cache.initialized.connect(self._on_cache_initialized)
        
    def init_page(self):
        """Initialize page components."""
        try:
            self.logger.debug("Initializing proximity page components")
            
            if not self._handlers_initialized:
                self._init_handlers()
                
            if not self._ui_initialized:
                self._init_ui_components()
                
            self.logger.debug("Proximity page components initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing proximity page: {e}", exc_info=True)
            self.context.ui_service.show_error("Initialization Error", str(e))
            raise
            
    def _init_handlers(self):
        """Initialize handlers safely."""
        try:
            self.logger.debug("Initializing handlers")
            
            # Create and initialize visualization handler
            self.visualization_handler = VisualizationHandler(
                self.context,
                self.playlists_dir
            )
            if not self.visualization_handler.initialize():  # Add this line
                raise RuntimeError("Failed to initialize visualization handler")
            
            # Connect handler signals
            self.visualization_handler.visualization_ready.connect(self._on_visualization_ready)
            self.visualization_handler.error_occurred.connect(self._on_visualization_error)
            
            self._handlers_initialized = True
            
        except Exception as e:
            self.logger.error(f"Error initializing handlers: {e}")
            self.context.ui_service.show_error("Handler Initialization Error", str(e))
            raise
            
    def _init_ui_components(self):
        """Initialize UI components safely."""
        try:
            # Create loading overlay
            self.loading_overlay = QWidget(self)
            overlay_layout = QVBoxLayout(self.loading_overlay)
            overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            loading_label = QLabel("Initializing visualization...", self.loading_overlay)
            loading_label.setFont(QFont("Segoe UI", 12))
            loading_label.setStyleSheet("color: white;")
            overlay_layout.addWidget(loading_label)
            
            self.loading_progress = QProgressBar(self.loading_overlay)
            self.loading_progress.setFixedWidth(300)
            self.loading_progress.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 2px;
                    background-color: #2D2D2D;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0078D4;
                    border-radius: 2px;
                }
            """)
            overlay_layout.addWidget(self.loading_progress)
            
            self.loading_overlay.setStyleSheet("""
                QWidget {
                    background-color: #202020;
                }
            """)
            
            # Create main widget to hold visualization
            self.visualization_widget = QWidget(self)
            self.visualization_widget.setObjectName("visualization_container")
            self.visualization_widget.hide()  # Hide until ready
            
            # Create layout
            layout = QVBoxLayout(self.visualization_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Create web view in main thread
            self.web_view = QWebEngineView()
            self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            
            # Add status panel
            self.status_panel = StatusPanel(self.state)
            layout.addWidget(self.status_panel)
            
            # Add to layout
            layout.addWidget(self.web_view)
            
            self._ui_initialized = True
            
        except Exception as e:
            self.logger.error(f"Error initializing UI: {e}")
            raise
        
    def setup_ui(self):
        """Set up the main UI layout."""
        if hasattr(self, '_layout'):
            return
            
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        
        # Create container frame
        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #202020;
                border: none;
            }
        """)
        
        # Container layout
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Add loading overlay first
        container_layout.addWidget(self.loading_overlay)
        
        # Add visualization widget
        container_layout.addWidget(self.visualization_widget)
        
        # Add to main layout
        self._layout.addWidget(container)
        
        # Connect signals if needed
        if not self._signals_connected:
            self.connect_signals()
            self._signals_connected = True
            
    def connect_signals(self):
        """Connect all component signals."""
        try:
            # Connect web view signals
            self.web_view.loadFinished.connect(self._on_load_finished)
            
            # Connect state signals
            self.state.visualization_updated.connect(self._on_visualization_updated)
            self.state.error_occurred.connect(self._on_state_error)
            
            self._signals_connected = True
            
        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}")
            self.context.ui_service.show_error("Signal Connection Error", str(e))
            
    def _on_cache_initialized(self):
        """Handle cache initialization completion."""
        self.logger.debug("Cache initialization complete")
        self._cache_initialized = True
        self.loading_progress.setValue(50)
        
        if hasattr(self, 'visualization_handler'):
            self._try_update_visualization()
            
    def _try_update_visualization(self):
        """Attempt to update visualization if all conditions are met."""
        if not self._cache_initialized:
            self.logger.debug("Cache not initialized, deferring visualization")
            return False
            
        if not self._ui_initialized:
            self.logger.debug("UI not initialized, deferring visualization")
            return False
            
        try:
            self.loading_progress.setValue(75)
            success = self.visualization_handler.update_visualization()
            
            if success:
                self.loading_progress.setValue(100)
                self.loading_overlay.hide()
                self.visualization_widget.show()
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating visualization: {e}")
            self.context.ui_service.show_error("Visualization Error", str(e))
            return False
            
    def _on_load_finished(self, ok: bool):
        """Handle web view load completion."""
        if ok:
            self.logger.debug("Visualization loaded successfully")
            if hasattr(self, 'visualization_handler'):
                self.visualization_handler.setup_web_channel(self.web_view)
        else:
            self.logger.error("Failed to load visualization")
            self.context.ui_service.show_error(
                "Visualization Error",
                "Failed to load network visualization"
            )
            
    def _on_visualization_ready(self, html_path: str):
        """Handle visualization HTML ready."""
        try:
            self.web_view.setUrl(QUrl.fromLocalFile(html_path))
        except Exception as e:
            self.logger.error(f"Error loading visualization: {e}")
            self.context.ui_service.show_error(
                "Visualization Error",
                "Failed to display visualization"
            )
            
    def _on_visualization_error(self, error: str):
        """Handle visualization errors."""
        self.logger.error(f"Visualization error: {error}")
        self.context.ui_service.show_error("Visualization Error", error)
            
    def _on_visualization_updated(self):
        """Handle visualization update completion."""
        self.state.set_status("Visualization updated successfully")
        
    def _on_state_error(self, error: str):
        """Handle state errors."""
        self.context.ui_service.show_error("State Error", error)
        
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        try:
            # Initialize if needed
            if self._is_first_show:
                self.init_page()
                self.setup_ui()
                self._is_first_show = False
                
            # Show loading overlay
            self.loading_overlay.show()
            self.visualization_widget.hide()
            self.loading_progress.setValue(25)
                
            # Update visualization
            self._try_update_visualization()
                
        except Exception as e:
            self.logger.error(f"Error in show event: {e}", exc_info=True)
            self.context.ui_service.show_error("Show Event Error", str(e))
            
    def hideEvent(self, event):
        """Handle hide event."""
        try:
            super().hideEvent(event)
            self.logger.debug("Hiding proximity page")
            
            # Cache state before hiding
            if hasattr(self, 'state'):
                self.state.cache_current_state()
                
        except Exception as e:
            self.logger.error(f"Error in hide event: {e}")
            self.context.ui_service.show_error("Hide Event Error", str(e))
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Starting proximity page cleanup")
            
            # Clean up visualization handler
            if hasattr(self, 'visualization_handler'):
                self.visualization_handler.cleanup()
                self.visualization_handler = None
                
            # Clean up web view
            if hasattr(self, 'web_view'):
                self.web_view.setUrl(QUrl())
                self.web_view.deleteLater()
                self.web_view = None
                
            # Clean up status panel
            if hasattr(self, 'status_panel'):
                self.status_panel.cleanup()
                self.status_panel = None
                
            # Reset flags
            self._ui_initialized = False
            self._handlers_initialized = False
            self._signals_connected = False
            self._cache_initialized = False
            
            # Remove layout
            if hasattr(self, '_layout'):
                QWidget().setLayout(self._layout)
                delattr(self, '_layout')
                
            # Call parent cleanup
            super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during proximity page cleanup: {e}", exc_info=True)
            self.context.ui_service.show_error("Cleanup Error", str(e))