# gui/windows/pages/proximity/proximity_page.py

from pathlib import Path
import logging
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QFrame, QSizePolicy, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl
import weakref

from app.config import Config
from gui.windows.pages.base_page import BasePage
from core.context import ApplicationContext
from .state import ProximityState
from .handlers.visualization_handler import VisualizationHandler

class ProximityPage(BasePage):
    """Page for visualizing playlist relationships."""
    
    def __init__(self, parent=None):
        # Initialize logger first
        super().__init__(parent)
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.context = ApplicationContext.get_instance()
        self.logger = logging.getLogger('proximity_page')
        self.logger.setLevel(logging.DEBUG)
        
        # Initialize state
        self.state = ProximityState()
        
        # Initialize tracking flags
        self._initialization_complete = False
        self._web_channel_setup = False
        self._visualization_loaded = False
        
        # Set up UI and handlers
        self.init_page()
        self.setup_ui()
        
        # Connect to cache initialization
        self.context.cache.initialized.connect(self._on_cache_initialized)
        
    def init_page(self):
        """Initialize page components."""
        try:
            self.logger.debug("Starting proximity page initialization")
            
            # Create and initialize visualization handler
            self.visualization_handler = VisualizationHandler(
                self.context,
                self.playlists_dir
            )
            if not self.visualization_handler.initialize():
                raise RuntimeError("Failed to initialize visualization handler")
            
            # Connect handler signals - use weak references to prevent circular refs
            self.visualization_handler.error_occurred.connect(self._on_visualization_error)
            self.visualization_handler.visualization_ready.connect(self._on_visualization_ready)
            
            self._initialization_complete = True
            self.logger.debug("Proximity page initialization complete")
            
        except Exception as e:
            self.logger.error(f"Error initializing proximity page: {e}", exc_info=True)
            self.context.ui_service.show_error("Initialization Error", str(e))
            raise
            
    def setup_ui(self):
        """Set up the main UI layout. Called once during initialization."""
        if hasattr(self, '_layout'):
            self.logger.debug("UI already set up")
            return
            
        self.logger.debug("Setting up proximity page UI")
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)       
        
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
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create visualization widget
        self.visualization_widget = QWidget(self)
        self.visualization_widget.setObjectName("visualization_container")
        self.visualization_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)       
        
        # Create layout
        layout = QVBoxLayout(self.visualization_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.visualization_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # Create web view with proper window flags
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(760)  # Or some reasonable minimum
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, False)  # Ensure explicit show/hide control
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)  # Prevent system background
        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.web_view.loadFinished.connect(self._on_load_finished)
        layout.addWidget(self.web_view)
        
        # Add visualization widget to container
        container_layout.addWidget(self.visualization_widget)
        
        # Add to main layout
        self._layout.addWidget(container)
        
        self.logger.debug("UI setup complete")
        
    def _on_visualization_ready(self, html_path: str):
        """Handle visualization HTML ready."""
        if self._visualization_loaded:
            self.logger.debug("Ignoring duplicate visualization ready signal")
            return
            
        try:
            self.logger.debug(f"Loading visualization from {html_path}")
            self.web_view.load(QUrl.fromLocalFile(html_path))
        except Exception as e:
            self.logger.error(f"Error loading visualization: {e}")
            self.context.ui_service.show_error("Visualization Error", str(e))
            
    def _on_load_finished(self, ok: bool):
        """Handle web view load completion."""
        if self._web_channel_setup:
            self.logger.debug("Ignoring duplicate load finished signal")
            return
            
        self.logger.debug(f"Web view load finished: {'success' if ok else 'failed'}")
        if ok:
            self._visualization_loaded = True
            if hasattr(self, 'visualization_handler'):
                self.visualization_handler.setup_web_channel(self.web_view)
                self._web_channel_setup = True
                self.logger.debug("Web channel setup complete")
        else:
            self.logger.error("Failed to load visualization")
            self.context.ui_service.show_error(
                "Visualization Error",
                "Failed to load network visualization"
            )
            
    def _on_visualization_error(self, error: str):
        """Handle visualization errors."""
        self.logger.error(f"Visualization error: {error}")
        self.context.ui_service.show_error("Visualization Error", error)
            
    def _on_cache_initialized(self):
        """Handle cache initialization completion."""
        self.logger.debug("Cache initialization complete")
        self._try_update_visualization()
            
    def _try_update_visualization(self):
        """Attempt to update visualization if all conditions are met."""
        if not self.context.cache.is_initialized:
            self.logger.debug("Cache not initialized, deferring visualization")
            return False
                
        try:
            self.logger.debug("Attempting to update visualization")
            success = self.visualization_handler.update_visualization()
            self.logger.debug(f"Visualization update {'successful' if success else 'failed'}")
            return success
                
        except Exception as e:
            self.logger.error(f"Error updating visualization: {e}")
            self.context.ui_service.show_error("Visualization Error", str(e))
            return False
            
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.logger.debug("Show event triggered")
        self._try_update_visualization()
            
    def hideEvent(self, event):
        """Handle hide event."""
        self.logger.debug("Hide event triggered")
        try:
            super().hideEvent(event)
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
                delattr(self, 'visualization_handler')
                
            # Clean up web view
            if hasattr(self, 'web_view'):
                self.web_view.setUrl(QUrl())
                self.web_view.deleteLater()
                delattr(self, 'web_view')
                
            # Reset flags
            self._initialization_complete = False
            self._web_channel_setup = False
            self._visualization_loaded = False
            
            # Call parent cleanup
            super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during proximity page cleanup: {e}", exc_info=True)
            self.context.ui_service.show_error("Cleanup Error", str(e))