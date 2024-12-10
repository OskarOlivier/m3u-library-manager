# gui/windows/pages/proximity/visualization/web_bridge.py

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
import logging
from typing import Optional

class JSBridge(QObject):
    """Separate class to handle JavaScript communication."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('js_bridge')
        
    @pyqtSlot(str)
    def debugLog(self, message: str):
        """Handle incoming JavaScript log messages."""
        try:
            if message.startswith('[ERROR]'):
                self.logger.error(message[8:])
            elif message.startswith('[WARN]'):
                self.logger.warning(message[7:])
            elif message.startswith('[DEBUG]'):
                self.logger.debug(message[8:])
            else:
                self.logger.info(message)
        except Exception as e:
            self.logger.error(f"Error handling JS log: {e}")

class WebChannelBridge(QObject):
    """Bridges communication between JavaScript and Qt using WebChannel."""
    
    channel_ready = pyqtSignal()
    
    def __init__(self, web_view: QWebEngineView, network_handler: 'NetworkEventHandler'):
        super().__init__(web_view)  # Set parent to ensure proper lifecycle
        
        # Initialize logger
        self.logger = logging.getLogger('web_bridge')
        self.logger.setLevel(logging.DEBUG)
        
        # Store references
        self._web_view = web_view
        self._network_handler = network_handler
        
        # Initialize components
        self._channel = None
        self._js_bridge = None
        self._initialized = False
        
        # Set up channel
        self._setup_channel()
        
    def _setup_channel(self):
        """Set up WebChannel and bridge objects."""
        try:
            self.logger.debug("Setting up initial WebChannel")
            
            # Create new channel with parent
            self._channel = QWebChannel(self)
            
            # Create JS bridge with channel as parent
            self._js_bridge = JSBridge(self._channel)
            
            # Register objects
            self._channel.registerObject("networkHandler", self._js_bridge)
            self._network_handler.moveToThread(self.thread())
            self._channel.registerObject("networkEvents", self._network_handler)
            
            # Set channel on page
            if self._web_view and self._web_view.page():
                self._web_view.page().setWebChannel(self._channel)
                
                # Connect page signals
                page = self._web_view.page()
                page.loadStarted.connect(self._on_load_started)
                page.loadFinished.connect(self._on_load_finished)
                
            self.logger.debug("WebChannel setup complete")
            
        except Exception as e:
            self.logger.error(f"WebChannel setup failed: {e}", exc_info=True)
            raise

    def _on_load_started(self):
        """Handle page load start."""
        self.logger.debug("Page load started")
        
    def _on_load_finished(self, ok: bool):
        """Handle page load completion."""
        if not ok:
            self.logger.error("Page load failed")
            return
            
        self.logger.debug("Page load complete - initializing bridge")
        self._inject_bridge_checks()
        
    def _inject_bridge_checks(self):
        """Inject JavaScript to verify bridge."""
        if not self._web_view or not self._web_view.page():
            self.logger.error("Cannot inject bridge checks - no valid page")
            return
            
        check_js = """
            console.log('Environment check:', {
                'QWebChannel exists': typeof QWebChannel !== 'undefined',
                'qt exists': typeof qt !== 'undefined',
                'qt.webChannelTransport exists': qt && typeof qt.webChannelTransport !== 'undefined'
            });

            if (qt && qt.webChannelTransport) {
                try {
                    new QWebChannel(qt.webChannelTransport, function(channel) {
                        window.bridge = channel.objects.networkHandler;
                        window.events = channel.objects.networkEvents;
                        console.log('Bridge setup complete:', !!window.bridge);
                    });
                } catch (e) {
                    console.error('Bridge setup error:', e);
                }
            }
        """
        
        try:
            self._web_view.page().runJavaScript(check_js)
            self.logger.debug("Bridge checks injected")
        except Exception as e:
            self.logger.error(f"Failed to inject bridge checks: {e}")

    def cleanup(self):
        """Clean up bridge resources."""
        try:
            self.logger.debug("Starting bridge cleanup")
            
            # Disconnect page signals
            if self._web_view and self._web_view.page():
                try:
                    page = self._web_view.page()
                    page.loadStarted.disconnect(self._on_load_started)
                    page.loadFinished.disconnect(self._on_load_finished)
                except:
                    pass
                
            # Clean up channel
            if self._channel:
                try:
                    if self._js_bridge:
                        self._channel.deregisterObject(self._js_bridge)
                    if self._network_handler:
                        self._channel.deregisterObject(self._network_handler)
                except:
                    pass
                    
            # Clear references
            self._web_view = None
            self._network_handler = None
            self._channel = None
            self._js_bridge = None
            self._initialized = False
            
            self.logger.debug("Bridge cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during bridge cleanup: {e}")