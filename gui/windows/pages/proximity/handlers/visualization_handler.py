# gui/windows/pages/proximity/handlers/visualization_handler.py

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from pathlib import Path
import tempfile
import codecs
from typing import Dict, List, Optional, Set
import logging

from utils.m3u.parser import read_m3u
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
        
        # Initialize components
        self.html_generator = VisualizationHTMLGenerator()
        self.network_handler = None
        self.web_bridge = None
        self.temp_html_path = None
        self.web_view = None
        
        # Track states
        self.selected_node: Optional[str] = None
        self.highlighted_nodes: Set[str] = set()
        self._is_updating = False
        self._web_channel_setup = False
        self._visualization_ready = False
        
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
                
            if self._web_channel_setup:
                self.logger.debug("Web channel already set up")
                return True
                
            self.web_view = web_view
            
            # Create network handler
            if not self.network_handler:
                self.network_handler = NetworkEventHandler()
            
            # Create web bridge
            if not self.web_bridge:
                self.web_bridge = WebChannelBridge(
                    web_view,
                    self.network_handler
                )
            
            # Connect network handler signals if not already connected
            self._connect_network_signals()
            
            self._web_channel_setup = True
            self.update_status("Web channel setup complete")
            return True
            
        except Exception as e:
            self.report_error(f"Web channel setup failed: {str(e)}")
            return False
            
    def _connect_network_signals(self):
        """Connect network handler signals."""
        if not self.network_handler:
            return
            
        # Safely disconnect any existing connections first
        try:
            self.network_handler.node_selected.disconnect()
            self.network_handler.node_hovered.disconnect()
            self.network_handler.error_occurred.disconnect()
            self.network_handler.stabilization_complete.disconnect()
            self.network_handler.stabilization_progress.disconnect()
        except:
            pass
            
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
                
            if self._is_updating:
                self.logger.debug("Visualization update already in progress")
                return False
                
            self._is_updating = True
            self.update_status("Generating visualization...")
            
            # Generate data
            nodes_data, edges_data = self._generate_network_data()
            
            # Generate HTML
            html_content = self.html_generator.generate_html(nodes_data, edges_data)
            
            # Write to temp file
            if not self.temp_html_path:
                self.temp_html_path = Path(tempfile.gettempdir()) / "playlist_network.html"
                
            with codecs.open(self.temp_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            # Emit ready signal
            self._visualization_ready = True
            self.visualization_ready.emit(str(self.temp_html_path))
            self.update_status("Visualization updated")
            return True
            
        except Exception as e:
            self.report_error(f"Failed to update visualization: {str(e)}")
            return False
        finally:
            self._is_updating = False
            
    def _generate_network_data(self) -> tuple[List[Dict], List[Dict]]:
        """Generate nodes and edges data from relationships."""
        nodes_data = []
        edges_data = []

        try:
            # Get regular playlists
            from utils.playlist import get_regular_playlists
            playlists = get_regular_playlists(self.playlists_dir)
            
            # Track processed edges to avoid duplicates
            processed_edges = set()
            
            # First pass: Create nodes and collect track counts
            for playlist_path in playlists:
                track_count = len(read_m3u(str(playlist_path))) or 1
                nodes_data.append({
                    'id': str(playlist_path),
                    'label': playlist_path.stem,
                    'value': track_count,
                    'title': f"{playlist_path.stem}\n{track_count} tracks"
                })
                
                # Get relationships
                relationships = self.relationship_cache.get_related_playlists(
                    str(playlist_path)
                )
                
                # Create edges (avoiding duplicates)
                for target_id, strength in relationships.items():
                    edge_key = tuple(sorted([str(playlist_path), target_id]))
                    if edge_key not in processed_edges:
                        edges_data.append({
                            'from': str(playlist_path),
                            'to': target_id,
                            'value': strength * 10,
                            'title': f"{strength} tracks in common"
                        })
                        processed_edges.add(edge_key)
                        
            return nodes_data, edges_data
                
        except Exception as e:
            self.report_error(f"Error generating network data: {str(e)}")
            raise
            
    def _handle_node_selected(self, node_id: str):
        """Handle node selection from network."""
        if node_id == self.selected_node:
            return
            
        self.selected_node = node_id
        self.node_selected.emit(node_id)
        
        try:
            # Update relationships
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
            self._is_updating = False
            self._web_channel_setup = False
            self._visualization_ready = False
            
        except Exception as e:
            self.report_error(f"Error during cleanup: {str(e)}")