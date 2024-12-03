# gui/windows/pages/proximity/handlers/visuali\.py

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from pathlib import Path
import tempfile
import codecs
import logging
from typing import Dict, List, Optional, Set

from core.handlers.base_handler import BaseHandler
from core.context import ApplicationContext
from ..visualization.web_bridge import WebChannelBridge
from ..visualization.network_handler import NetworkEventHandler
from ..visualization.html_generator import VisualizationHTMLGenerator

class VisualizationHandler(BaseHandler):
    """Handles network visualization generation and interaction."""
    
    # Visualization-specific signals
    visualization_ready = pyqtSignal(str)  # Emits path to HTML file
    node_selected = pyqtSignal(str)  # Emits node ID
    node_updated = pyqtSignal(str, float)  # Emits node ID and strength
    node_hovered = pyqtSignal(str)  # Emits hovered node ID
    view_stabilized = pyqtSignal()  # Emits when network view stabilizes
    
    def __init__(self, context: ApplicationContext, playlists_dir: Path):
        super().__init__("visualization_handler")
        self.context = context
        self.playlists_dir = playlists_dir
        self.relationship_cache = context.cache
        
        # Add cache initialization tracking
        self._cache_ready = False
        self.relationship_cache.initialized.connect(self._on_cache_initialized)

        # Initialize components
        self.html_generator = VisualizationHTMLGenerator()
        self.network_handler = None
        self.web_bridge = None
        self.temp_html_path = None
        self.web_view = None
        
        # Track selected nodes
        self.selected_node: Optional[str] = None
        self.highlighted_nodes: Set[str] = set()
        
    def _do_initialize(self) -> bool:
        """Initialize visualization components."""
        if not self.html_generator.has_resources:
            self.report_error("Failed to load visualization resources")
            return False
        
        self.update_status("Visualization handler initialized")
        return True
        
    def setup_web_channel(self, web_view: QWebEngineView) -> bool:
        """Set up WebChannel communication."""
        try:
            if not self.is_initialized:
                self.report_error("Handler not initialized")
                return False
                
            self.web_view = web_view
            
            # Create network handler
            self.network_handler = NetworkEventHandler()
            
            # Create web bridge
            self.web_bridge = WebChannelBridge(
                web_view,
                self.network_handler
            )
            
            # Connect network handler signals
            self._connect_network_signals()
            
            self.update_status("Web channel setup complete")
            return True
            
        except Exception as e:
            self.report_error(f"Web channel setup failed: {str(e)}")
            return False
            
    def _connect_network_signals(self):
        """Connect network handler signals."""
        if not self.network_handler:
            return
            
        # Forward relevant signals
        self.network_handler.node_selected.connect(self._handle_node_selected)
        self.network_handler.node_hovered.connect(self.node_hovered)
        self.network_handler.error_occurred.connect(self.error_occurred)
        self.network_handler.stabilization_complete.connect(self.view_stabilized)
        
        # Connect progress updates
        self.network_handler.stabilization_progress.connect(self.update_progress)
        
    def update_visualization(self) -> bool:
        """Generate and update the network visualization."""
        try:
            if not self.is_initialized:
                self.report_error("Handler not initialized")
                return False
                
            if not self.relationship_cache.is_initialized:
                self.logger.warning("Cache not initialized")
                return False
                
            self.update_status("Generating visualization...")
            
            # Generate data
            nodes_data, edges_data = self._generate_network_data()
            
            if not nodes_data:
                self.logger.warning("No nodes data generated")
                return False
                
            # Generate HTML
            html_content = self.html_generator.generate_html(nodes_data, edges_data)
            
            # Write to temp file
            if not self.temp_html_path:
                self.temp_html_path = Path(tempfile.gettempdir()) / "playlist_network.html"
                
            with codecs.open(self.temp_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            # Emit ready signal
            self.visualization_ready.emit(str(self.temp_html_path))
            self.update_status("Visualization updated")
            return True
            
        except Exception as e:
            self.report_error(f"Failed to update visualization: {str(e)}")
            return False
            
    def _on_cache_initialized(self):
        """Handle cache initialization completion."""
        self._cache_ready = True
        self.update_status("Cache initialized")
            
    def _generate_network_data(self) -> tuple[List[Dict], List[Dict]]:
        """Generate nodes and edges data from relationships."""
        nodes_data = []
        edges_data = []
        
        try:
            # Get regular playlists
            from utils.playlist import get_regular_playlists
            playlists = get_regular_playlists(self.playlists_dir)
            
            # Create nodes
            for playlist_path in playlists:
                nodes_data.append({
                    'id': str(playlist_path),
                    'label': playlist_path.stem,
                    'value': 1  # Default size
                })
                
                # Get relationships for edges
                relationships = self.relationship_cache.get_related_playlists(
                    str(playlist_path)
                )
                for target_id, strength in relationships.items():
                    # Avoid duplicate edges by using consistent ordering
                    if str(playlist_path) < target_id:
                        edges_data.append({
                            'from': str(playlist_path),
                            'to': target_id,
                            'value': strength,  # Scale for visibility
                            'title': f"{strength} similarity"
                        })
                        
            return nodes_data, edges_data
            
        except Exception as e:
            self.report_error(f"Error generating network data: {str(e)}")
            raise
            
    def _handle_node_selected(self, node_id: str):
        """Handle node selection from network."""
        try:
            if node_id == self.selected_node:
                return
                
            self.selected_node = node_id
            self.node_selected.emit(node_id)
            
            # Get relationships
            relationships = self.relationship_cache.get_related_playlists(node_id)
            self.highlighted_nodes = set(relationships.keys())
            
            # Update node values
            if self.web_bridge and self.web_view:
                self._update_node_values(node_id, relationships)
                
        except Exception as e:
            self.report_error(f"Error handling node selection: {str(e)}")
            
    def _update_node_values(self, selected_id: str, relationships: Dict[str, float]):
        """Update node values based on relationships."""
        if not self.web_view:
            return
            
        try:
            # Update selected node
            script = f"""
                nodes.update([{{
                    id: '{selected_id}',
                    value: 2
                }}]);
            """
            
            # Update related nodes
            for target_id, strength in relationships.items():
                script += f"""
                    nodes.update([{{
                        id: '{target_id}',
                        value: {1 + strength}
                    }}]);
                """
                
            self.web_view.page().runJavaScript(script)
            
        except Exception as e:
            self.report_error(f"Error updating node values: {str(e)}")
            
    def _do_cleanup(self):
        """Clean up visualization resources."""
        try:
            # Clean up network handler
            if self.network_handler:
                self.network_handler.cleanup()
                self.network_handler = None
                
            # Clean up web bridge
            if self.web_bridge:
                self.web_bridge.cleanup()
                self.web_bridge = None
                
            # Clean up temp file
            if self.temp_html_path and self.temp_html_path.exists():
                self.temp_html_path.unlink()
                self.temp_html_path = None
                
            # Reset state
            self.selected_node = None
            self.highlighted_nodes.clear()
            self.web_view = None
            
        except Exception as e:
            self.report_error(f"Error during cleanup: {str(e)}")