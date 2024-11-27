# gui/windows/pages/proximity/proximity_page.py

from pathlib import Path
import logging
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import tempfile
import codecs
import json

from core.events.event_bus import Event, EventBus, EventType
from app.config import Config
from gui.windows.pages.base_page import BasePage
from core.cache.relationship_cache import RelationshipCache

class ProximityPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache = RelationshipCache.get_instance()
        self.event_bus = EventBus.get_instance()
        self.logger = logging.getLogger('proximity_page')
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.relationship_cache = RelationshipCache.get_instance()

        # Connect to cache events
        if not self.cache.is_initialized:
            self.cache.initialized.connect(self._on_cache_ready)
            
        self.event_bus.event_occurred.connect(self._handle_event)        
        
        # Load vis.js library content
        resources_dir = Path(__file__).parent.parent.parent.parent / 'resources'
        try:
            with open(resources_dir / 'vis-network.min.js', 'r', encoding='utf-8') as f:
                self.vis_js = f.read()
            with open(resources_dir / 'vis-network.min.css', 'r', encoding='utf-8') as f:
                self.vis_css = f.read()
        except Exception as e:
            self.logger.error(f"Failed to load vis.js resources: {e}")
            self.vis_js = ""
            self.vis_css = ""
        
        self.init_ui()
        self.update_visualization()
        
    def init_ui(self):
        self.logger.debug("Setting up UI")
        self.layout = QVBoxLayout(self)
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_load_finished)
        self.web_view.loadProgress.connect(lambda p: self.logger.debug(f"Load progress: {p}%"))
        self.layout.addWidget(self.web_view)

    def _on_load_finished(self, ok):
        if ok:
            self.logger.info("Web view loaded successfully")
        else:
            self.logger.error("Failed to load web view")

    def update_visualization(self):
        """Update the network visualization."""
        if not self.cache.is_initialized:
            self.logger.debug("Cache not initialized, deferring visualization")
            return
            
        try:
            # Create nodes and edges
            nodes_data = []
            edges_data = []
            
            # Get all playlists
            from utils.playlist import get_regular_playlists
            playlists = get_regular_playlists(self.playlists_dir)
            
            # Create nodes (one per playlist)
            for playlist_path in playlists:
                nodes_data.append({
                    'id': str(playlist_path),
                    'label': playlist_path.stem,
                    'color': self._random_dark_color()
                })
                
                # Get relationships for edges
                relationships = self.cache.get_related_playlists(str(playlist_path))
                for target_id, strength in relationships.items():
                    if str(playlist_path) < target_id:  # Avoid duplicate edges
                        edges_data.append({
                            'from': str(playlist_path),
                            'to': target_id,
                            'value': strength * 10,
                            #'color': self._get_edge_color(strength)
                        })

            # Generate HTML with visualization
            html = self._generate_visualization_html(nodes_data, edges_data)
            
            # Write to temp file and display
            temp_path = Path(tempfile.gettempdir()) / "playlist_network.html"
            with codecs.open(temp_path, 'w', encoding='utf-8') as f:
                f.write(html)

            self.web_view.setUrl(QUrl.fromLocalFile(str(temp_path)))

        except Exception as e:
            self.logger.error(f"Error updating visualization: {e}", exc_info=True)

    def _random_dark_color(self):
        """Generate a random dark color."""
        import random
        r = random.randint(63, 127)
        g = random.randint(63, 127)
        b = random.randint(63, 127)
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _generate_visualization_html(self, nodes_data, edges_data):
        """Generate HTML for network visualization."""
        return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Playlist Network</title>
                <style type="text/css">
                    {self.vis_css}
                    #mynetwork {{
                        width: 100%;
                        height: 100vh;
                        background-color: #202020;
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                        background-color: #202020;
                    }}
                </style>
                <script type="text/javascript">
                    {self.vis_js}
                </script>
            </head>
            <body>
                <div id="mynetwork"></div>
                <script type="text/javascript">
                    const nodes = new vis.DataSet({json.dumps(nodes_data)});
                    const edges = new vis.DataSet({json.dumps(edges_data)});

                    const container = document.getElementById('mynetwork');
                    const data = {{ nodes, edges }};
                    const options = {{
                        nodes: {{
                            font: {{ color: 'white' }}
                        }},
                        edges: {{
                            color: {{ inherit: false }},
                            smooth: {{ type: 'continuous' }},
                            width: 2
                        }},
                        interaction: {{ hover: true }},
                        physics: {{
                            forceAtlas2Based: {{
                                gravitationalConstant: -100,
                                springLength: 100,
                                springConstant: 0.1
                            }},
                            minVelocity: 0.25,
                            solver: 'forceAtlas2Based'
                        }}
                    }};

                    const network = new vis.Network(container, data, options);

                    function hexToRgba(hex, alpha) {{
                        const r = parseInt(hex.slice(1, 3), 16);
                        const g = parseInt(hex.slice(3, 5), 16);
                        const b = parseInt(hex.slice(5, 7), 16);
                        return `rgba(${{r}}, ${{g}}, ${{b}}, ${{alpha}})`;
                    }}

                    network.on('selectNode', function(params) {{
                        const selectedNode = params.nodes[0];
                        const connectedNodes = network.getConnectedNodes(selectedNode);

                        nodes.forEach(node => {{
                            if (node.id === selectedNode || connectedNodes.includes(node.id)) {{
                                nodes.update({{
                                    id: node.id,
                                    color: node.originalColor,
                                    opacity: 1,
                                    font: {{ color: 'white' }}
                                }});
                            }} else {{
                                nodes.update({{
                                    id: node.id,
                                    color: node.originalColor,
                                    opacity: 0.2,
                                    font: {{ color: 'rgba(255,255,255,0.2)' }}
                                }});
                            }}
                        }});

                        edges.forEach(edge => {{
                            const isConnected = edge.from === selectedNode || edge.to === selectedNode;
                            const color = edge.originalColor;
                            const opacity = isConnected ? 1 : 0.2;
                            
                            edges.update({{
                                id: edge.id,
                                color: {{
                                    color: hexToRgba(color, opacity),
                                    hover: hexToRgba(color, 1)
                                }}
                            }});
                        }});
                    }});

                    network.on('deselectNode', function() {{
                        nodes.forEach(node => {{
                            nodes.update({{
                                id: node.id,
                                color: node.originalColor,
                                opacity: 1,
                                font: {{ color: 'white' }}
                            }});
                        }});

                        edges.forEach(edge => {{
                            edges.update({{
                                id: edge.id,
                                color: {{
                                    color: edge.originalColor,
                                    hover: edge.originalColor
                                }}
                            }});
                        }});
                    }});
                </script>
            </body>
            </html>
        """

    def _on_cache_ready(self):
        """Handle cache initialization completion."""
        self.update_visualization()
        
    def _handle_event(self, event: Event):
        """Handle events from the event bus."""
        if event.type == EventType.RELATIONSHIPS_CHANGED:
            self.update_visualization()

    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.logger.debug("Show event triggered - updating visualization")
        
        # Initialize cache if needed
        if not self.relationship_cache._initialized:
            # Use AsyncHelper to run initialization
            from gui.workers.async_base import AsyncHelper
            helper = AsyncHelper(self._initialize_cache())
            helper.start()
            
        self.update_visualization()
    
    async def _initialize_cache(self):
        """Initialize relationship cache with progress tracking."""
        try:
            self.logger.debug("Initializing relationship cache")
            await self.relationship_cache.initialize(
                self.playlists_dir,
                lambda p: self.logger.debug(f"Cache initialization progress: {p}%")
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize relationship cache: {e}")