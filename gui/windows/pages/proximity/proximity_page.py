# gui/windows/pages/proximity/proximity_page.py

from pathlib import Path
import logging
import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QFrame, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from app.config import Config
from gui.windows.pages.base_page import BasePage
from core.context import ApplicationContext
from utils.m3u.parser import read_m3u
from .state import ProximityState
from .visualization.graph_widget import PlaylistGraphWidget
from .visualization.layout_manager import ForceAtlas2Layout
from .visualization.interaction import GraphInteractionHandler
from .visualization.styling import GraphStyles

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
        self._initialization_in_progress = False
        
        # Call parent constructor after initializing our attributes
        super().__init__(parent)
        
        # Connect to cache initialization
        self.context.cache.initialized.connect(self._on_cache_initialized)
    
    def init_page(self):
        """Initialize page components."""
        try:
            if self._initialization_in_progress:
                self.logger.debug("Initialization already in progress")
                return

            self._initialization_in_progress = True
            self.logger.debug("Starting proximity page initialization")

            # Cache should already be initialized by MainWindow
            if not self.context.cache.is_initialized:
                self.logger.error("Cache not initialized - this should not happen")
                self.context.ui_service.show_error(
                    "Initialization Error", 
                    "Cache not properly initialized"
                )
                return

            if not self._handlers_initialized:
                self._init_handlers()
                
            if not self._ui_initialized:
                self._init_ui_components()
                
            self.logger.debug("Proximity page components initialized")
            self._initialization_in_progress = False
            
            # Try to update visualization after initialization
            QTimer.singleShot(100, self._try_update_visualization)
            
        except Exception as e:
            self._initialization_in_progress = False
            self.logger.error(f"Error initializing proximity page: {e}", exc_info=True)
            self.context.ui_service.show_error("Initialization Error", str(e))
            raise

    def _on_cache_initialized(self):
        """Handle cache initialization completion."""
        self.logger.debug("Cache initialization complete")
        self._cache_initialized = True
        
        if hasattr(self, 'loading_progress'):
            self.loading_progress.setValue(50)
            
        QTimer.singleShot(100, self._try_update_visualization)
           
    def _init_handlers(self):
        """Initialize handlers safely."""
        try:
            self.logger.debug("Initializing handlers")
            
            # Create layout manager
            self.layout_manager = ForceAtlas2Layout()
            
            # Create interaction handler
            self.interaction_handler = GraphInteractionHandler()
            
            # Connect handler signals
            self.layout_manager.layout_updated.connect(self._on_layout_updated)
            self.layout_manager.iteration_complete.connect(self._on_layout_iteration)
            
            self._handlers_initialized = True
            self.logger.debug("Handlers initialized successfully")
            
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
            loading_label.setFont(GraphStyles.LABEL_STYLES['base_font'])  # Using the QFont object
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
            
            self.loading_overlay.setStyleSheet(f"""
                QWidget {{
                    background-color: {GraphStyles.COLORS['background']};
                }}
            """)
            
            # Create visualization widget
            self.visualization_widget = PlaylistGraphWidget(self)
            self.visualization_widget.setObjectName("visualization_widget")
            self.visualization_widget.hide()  # Hide until ready
            
            # Connect visualization signals
            self.visualization_widget.node_selected.connect(self._on_node_selected)
            self.visualization_widget.node_hovered.connect(self._on_node_hovered)
            self.visualization_widget.layout_stabilized.connect(self._on_layout_stabilized)
            
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
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {GraphStyles.COLORS['background']};
                border: none;
            }}
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
            
    def _try_update_visualization(self):
        """Attempt to update visualization if all conditions are met."""
        try:
            self.logger.debug("Attempting to update visualization")
            
            if not self.context.cache.is_initialized:
                self.logger.debug("Cache not initialized, deferring visualization")
                return False
                
            if not self._ui_initialized:
                self.logger.debug("UI not initialized, deferring visualization")
                return False
                
            self.loading_progress.setValue(75)
            
            # Generate visualization data
            nodes_data, edges_data = self._generate_visualization_data()
            
            # Update graph - this will initialize the layout internally
            self.visualization_widget.update_graph(nodes_data, edges_data)
            
            self.loading_progress.setValue(100)
            QTimer.singleShot(500, self._show_visualization)
            return True
                
        except Exception as e:
            self.logger.error(f"Error updating visualization: {e}")
            self.context.ui_service.show_error("Visualization Error", str(e))
            return False
            
    def _generate_visualization_data(self):
        nodes_data = []
        edges_data = []
        
        try:
            # Get regular playlists
            from utils.playlist import get_regular_playlists
            playlists = get_regular_playlists(self.playlists_dir)
            
            for playlist_path in playlists:
                # Get track count for mass calculation
                tracks = len(read_m3u(str(playlist_path)))
                nodes_data.append({
                    'id': str(playlist_path),
                    'label': playlist_path.stem,
                    'value': tracks,  # Track count determines size and mass
                    'mass': 1 + np.log1p(tracks) * 0.2  # Logarithmic scaling for mass
                })
                
                # Get relationships for edges
                relationships = self.context.cache.get_related_playlists(
                    str(playlist_path)
                )
                for target_id, strength in relationships.items():
                    if str(playlist_path) < target_id:
                        edges_data.append({
                            'from': str(playlist_path),
                            'to': target_id,
                            'value': strength
                        })
                        
            return nodes_data, edges_data
            
        except Exception as e:
            self.logger.error(f"Error generating visualization data: {e}")
            raise
            
    def _on_layout_updated(self, positions):
        """Handle layout update."""
        self.visualization_widget.update_positions(positions)
        
    def _on_layout_iteration(self, iteration):
        """Handle layout iteration progress."""
        progress = min(100, int((iteration / 100) * 100))  # Ensure integer value
        if hasattr(self, 'loading_progress'):
            self.loading_progress.setValue(75 + int(progress * 0.25))  # Convert to integer
        
    def _on_layout_stabilized(self):
        """Handle layout stabilization."""
        if hasattr(self, 'loading_progress'):
            self.loading_progress.setValue(100)
            
    def _on_node_selected(self, node_id: str):
        """Handle node selection."""
        self.state.select_node(node_id)
        
    def _on_node_hovered(self, node_id: str):
        """Handle node hover."""
        # Update state if needed
        pass
        
    def _show_visualization(self):
        """Show visualization after loading."""
        try:
            self.logger.debug("Showing visualization")
            if hasattr(self, 'loading_overlay'):
                self.loading_overlay.hide()
            if hasattr(self, 'visualization_widget'):
                self.visualization_widget.show()
        except Exception as e:
            self.logger.error(f"Error showing visualization: {e}")
            
    def showEvent(self, event):
        """Handle show event."""
        try:
            self.logger.debug("Show event triggered")
            
            # Initialize if needed
            if self._is_first_show:
                self.logger.debug("First show - starting initialization")
                if hasattr(self, 'loading_overlay'):
                    self.loading_overlay.show()
                if hasattr(self, 'visualization_widget'):
                    self.visualization_widget.hide()
                if hasattr(self, 'loading_progress'):
                    self.loading_progress.setValue(25)
                
                # Start initialization process
                QTimer.singleShot(100, self.init_page)
                self._is_first_show = False
            else:
                self.logger.debug("Subsequent show - updating visualization")
                # Handle subsequent shows
                if hasattr(self, 'loading_overlay'):
                    self.loading_overlay.show()
                if hasattr(self, 'visualization_widget'):
                    self.visualization_widget.hide()
                QTimer.singleShot(100, self._try_update_visualization)
                
            super().showEvent(event)
                
        except Exception as e:
            self.logger.error(f"Error in show event: {e}", exc_info=True)
            self.context.ui_service.show_error("Show Event Error", str(e))
            
    def hideEvent(self, event):
        """Handle hide event."""
        try:
            self.logger.debug("Hide event triggered")
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
            
            # Clean up visualization widget
            if hasattr(self, 'visualization_widget'):
                self.visualization_widget.cleanup()
                self.visualization_widget = None
                
            # Clean up handlers
            if hasattr(self, 'layout_manager'):
                self.layout_manager.stop()
                
            if hasattr(self, 'interaction_handler'):
                self.interaction_handler = None
                
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