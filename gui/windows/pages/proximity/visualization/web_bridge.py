# gui/windows/pages/proximity/visualization/web_bridge.py

from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import logging

from .network_handler import NetworkEventHandler

class WebChannelBridge(QObject):
    """Bridges communication between JavaScript and Qt using WebChannel."""
    
    def __init__(self, web_view: QWebEngineView, network_handler: NetworkEventHandler):
        super().__init__()
        self.logger = logging.getLogger('web_bridge')
        self.web_view = web_view
        self.network_handler = network_handler
        self.channel = QWebChannel()
        
        # Set up bridge
        self.setup_bridge()
        
    def setup_bridge(self):
        """Set up WebChannel connection."""
        try:
            # Register network handler with channel
            self.channel.registerObject("networkHandler", self.network_handler)
            
            # Set channel for web page
            self.web_view.page().setWebChannel(self.channel)
            
            # Inject WebChannel JavaScript
            self.inject_channel_js()
            
        except Exception as e:
            self.logger.error(f"Error setting up web bridge: {e}")
            
    def inject_channel_js(self):
        """Inject WebChannel JavaScript into the page."""
        channel_js = """
            // Create WebChannel connection
            new QWebChannel(qt.webChannelTransport, function(channel) {
                // Store handler reference globally
                window.bridge = channel.objects.networkHandler;
                
                // Re-emit any existing events
                if (window.network) {
                    setupEventHandlers();
                }
            });
        """
        
        # Inject after page load
        self.web_view.page().loadFinished.connect(
            lambda ok: self.web_view.page().runJavaScript(channel_js)
            if ok else self.logger.error("Failed to load page for bridge injection")
        )
        
    def cleanup(self):
        """Clean up bridge resources."""
        try:
            self.logger.debug("Cleaning up web bridge")
            
            # Deregister objects
            self.channel.deregisterObject(self.network_handler)
            
            # Clean up channel
            self.web_view.page().setWebChannel(None)
            self.channel.deleteLater()
            
        except Exception as e:
            self.logger.error(f"Error during bridge cleanup: {e}")