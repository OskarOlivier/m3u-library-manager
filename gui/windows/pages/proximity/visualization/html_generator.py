# gui/windows/pages/proximity/visualization/html_generator.py

from pathlib import Path
import json
from typing import List, Dict
import logging

class VisualizationHTMLGenerator:
    """Generates HTML and JavaScript for network visualization."""
    
    def __init__(self):
        self.logger = logging.getLogger('visualization_generator')
        
        # Load visualization resources
        lib_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'lib' / 'vis-9.1.2'
        try:
            with open(lib_dir / 'vis-network.min.js', 'r', encoding='utf-8') as f:
                self.vis_js = f.read()
            with open(lib_dir / 'vis-network.css', 'r', encoding='utf-8') as f:
                self.vis_css = f.read()
        except Exception as e:
            self.logger.error(f"Failed to load visualization resources: {e}")
            self.vis_js = ""
            self.vis_css = ""

    def generate_html(self, nodes_data: List[Dict], edges_data: List[Dict]) -> str:
        """Generate complete HTML with visualization."""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Playlist Network</title>
            <style>
                {self.vis_css}
                html, body {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                    background-color: #202020;
                }}
                #visualization {{
                    width: 100%;
                    height: 100%;
                    background-color: #202020;
                }}
            </style>
        </head>
        <body>
            <div id="visualization"></div>
            
            <script type="text/javascript">
                {self.vis_js}
            </script>
            
            <script type="text/javascript">
                // Global variables
                let network = null;
                let nodes = null;
                let edges = null;
                
                // Configuration
                const options = {{
                    nodes: {{
                        shape: 'dot',
                        borderWidth: 2,
                        size: 30,
                        color: {{
                            background: '#4CAF50',
                            border: '#2E7D32',
                            highlight: {{
                                background: '#81C784',
                                border: '#4CAF50'
                            }}
                        }},
                        font: {{
                            color: '#FFFFFF',
                            size: 14,
                            face: 'Segoe UI'
                        }},
                        shadow: true
                    }},
                    edges: {{
                        width: 2,
                        color: {{
                            color: '#FFFFFF',
                            opacity: 0.3,
                            highlight: '#4CAF50'
                        }},
                        smooth: {{
                            type: 'continuous',
                            roundness: 0.5
                        }},
                        arrows: {{
                            to: {{
                                enabled: false
                            }}
                        }}
                    }},
                    physics: {{
                        barnesHut: {{
                            gravitationalConstant: -2000,
                            centralGravity: 0.3,
                            springLength: 95,
                            springConstant: 0.04,
                            damping: 0.09
                        }},
                        stabilization: {{
                            iterations: 1000,
                            updateInterval: 50
                        }}
                    }},
                    interaction: {{
                        hover: true,
                        tooltipDelay: 200,
                        hideEdgesOnDrag: true,
                        zoomView: true
                    }}
                }};

                // Initialize visualization
                function initializeNetwork() {{
                    try {{
                        // Create datasets
                        nodes = new vis.DataSet({json.dumps(nodes_data)});
                        edges = new vis.DataSet({json.dumps(edges_data)});
                        
                        // Get container
                        const container = document.getElementById('visualization');
                        
                        // Create network
                        network = new vis.Network(container, {{
                            nodes: nodes,
                            edges: edges
                        }}, options);
                        
                        // Set up event handlers
                        setupEventHandlers();
                        
                    }} catch (error) {{
                        console.error('Network initialization error:', error);
                        // Send error to Qt
                        if (window.qt) {{
                            window.qt.webChannel.objects.bridge.handleError(error.toString());
                        }}
                    }}
                }}

                // Event handlers
                function setupEventHandlers() {{
                    if (!network) return;

                    network.on('click', function(params) {{
                        if (params.nodes.length > 0) {{
                            const nodeId = params.nodes[0];
                            window.bridge.nodeSelected(nodeId);
                        }}
                    }});

                    network.on('zoom', function(params) {{
                        window.bridge.zoomChanged(params.scale);
                    }});

                    network.on('stabilizationProgress', function(params) {{
                        const progress = Math.round(params.iterations / params.total * 100);
                        window.bridge.stabilizationProgress(progress);
                    }});

                    network.on('stabilizationIterationsDone', function() {{
                        window.bridge.stabilizationComplete();
                    }});

                    network.on('hoverNode', function(params) {{
                        window.bridge.nodeHovered(params.node);
                    }});
                }}

                // Initialize when document is ready
                document.addEventListener('DOMContentLoaded', function() {{
                    initializeNetwork();
                }});

                // Error handling
                window.onerror = function(message, source, lineno, colno, error) {{
                    console.error('JavaScript error:', message);
                    if (window.bridge) {{
                        window.bridge.handleError(message);
                    }}
                    return false;
                }};
            </script>
        </body>
        </html>
        """

    @property
    def has_resources(self) -> bool:
        """Check if visualization resources are loaded."""
        return bool(self.vis_js and self.vis_css)