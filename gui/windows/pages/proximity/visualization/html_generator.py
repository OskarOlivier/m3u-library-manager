# gui/windows/pages/proximity/visualization/html_generator.py

from pathlib import Path
import json
from typing import List, Dict
import logging

class VisualizationHTMLGenerator:
    """Generates HTML and JavaScript for network visualization."""
    
    def __init__(self):
        self.logger = logging.getLogger('visualization_generator')
        
        # Resolve paths relative to project root
        self.static_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'static'
        self.lib_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'lib'
        
        # Required resources
        self.required_files = [
            self.lib_dir / 'd3-7.8.5' / 'd3.min.js',
            self.static_dir / 'js' / 'network' / 'core' / 'network.js',
            self.static_dir / 'js' / 'network' / 'core' / 'layouts.js',
            self.static_dir / 'js' / 'network' / 'core' / 'themes.js',
            self.static_dir / 'js' / 'network' / 'bridge.js',
            self.static_dir / 'js' / 'network' / 'initialization.js',
            self.static_dir / 'css' / 'network.css'
        ]
        
        # Verify resources on initialization
        self._verify_resources()

    def _verify_resources(self) -> None:
        """Verify all required resources exist."""
        missing = []
        for path in self.required_files:
            if not path.exists():
                missing.append(str(path))
                self.logger.error(f"Missing required resource: {path}")
                
        if missing:
            raise FileNotFoundError(
                "Missing required visualization resources:\n" + 
                "\n".join(missing)
            )
            
    @property
    def has_resources(self) -> bool:
        """Check if all required resources are available."""
        try:
            self._verify_resources()
            return True
        except FileNotFoundError:
            return False

    def generate_html(self, nodes_data: List[Dict], edges_data: List[Dict]) -> str:
        """Generate complete HTML with visualization."""
        if not self.has_resources:
            raise RuntimeError("Required resources not available")
            
        try:
            # Format paths for resources
            d3_path = self.lib_dir / 'd3-7.8.5' / 'd3.min.js'
            css_path = self.static_dir / 'css' / 'network.css'
            js_path = self.static_dir / 'js' / 'network' / 'initialization.js'
            
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Playlist Network</title>
                <link rel="stylesheet" type="text/css" href="{css_path.as_posix()}">
            </head>
            <body>
                <div class="network-container">
                    <div id="visualization"></div>
                    <div class="loading">Initializing visualization...</div>
                </div>

                <!-- Load D3.js first -->
                <script src="{d3_path.as_posix()}"></script>

                <!-- Load QtWebChannel -->
                <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                
                <!-- Load visualization modules -->
                <script type="module" src="{js_path.as_posix()}"></script>

                <!-- Initialize with data -->
                <script type="module">
                    async function updateVisualization() {{
                        if (window.networkManager) {{
                            await window.networkManager.updateData(
                                {json.dumps(nodes_data)},
                                {json.dumps(edges_data)}
                            );
                        }}
                    }}
                    
                    // Update once initialization is complete
                    const checkInterval = setInterval(() => {{
                        if (window.networkManager && window.networkManager.isInitialized) {{
                            clearInterval(checkInterval);
                            updateVisualization();
                        }}
                    }}, 100);
                    
                    // Clear interval after 5 seconds to prevent infinite checking
                    setTimeout(() => clearInterval(checkInterval), 5000);
                </script>
            </body>
            </html>
            """
            
        except Exception as e:
            self.logger.error(f"Failed to generate visualization HTML: {e}")
            raise