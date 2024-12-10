# gui/windows/pages/proximity/visualization/network_handler.py

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import logging
from typing import Optional, Dict, Any

class NetworkEventHandler(QObject):
    """Handles events from the network visualization JavaScript."""
    
    # UI update signals
    node_selected = pyqtSignal(str)  # Node ID
    node_hovered = pyqtSignal(str)   # Node ID
    nodes_selected = pyqtSignal(list) # List of node IDs (for future multi-select)
    zoom_changed = pyqtSignal(float)  # Zoom level
    error_occurred = pyqtSignal(str)  # Error message
    
    # Progress signals
    stabilization_progress = pyqtSignal(int)  # Progress percentage
    stabilization_complete = pyqtSignal()
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = logging.getLogger('network_handler')
        self.logger.setLevel(logging.INFO)        
        
        # Track current state
        self._current_node: Optional[str] = None
        self._selected_nodes: set[str] = set()
        self._current_zoom: float = 1.0
        self._is_stabilizing: bool = False
        
    @pyqtSlot(str)
    def debugLog(self, message: str):
        """Handle debug messages from JavaScript."""
        self.logger.debug(f"Network Physics: {message}")
        
    # Add decorator to existing slots
    @pyqtSlot(str)
    def nodeSelected(self, node_id: str):
        """Handle node selection from JavaScript."""
        try:
            self.logger.debug(f"Node selected: {node_id}")
            self._current_node = node_id
            self.node_selected.emit(node_id)
        except Exception as e:
            self._handle_error("Node selection error", e)
            
    @pyqtSlot(list)
    def nodesSelected(self, node_ids: list):
        """Handle multi-node selection from JavaScript."""
        try:
            self.logger.debug(f"Nodes selected: {node_ids}")
            self._selected_nodes = set(node_ids)
            self.nodes_selected.emit(node_ids)
        except Exception as e:
            self._handle_error("Multi-select error", e)
            
    @pyqtSlot(str)
    def nodeHovered(self, node_id: str):
        """Handle node hover from JavaScript."""
        try:
            self.logger.debug(f"Node hovered: {node_id}")
            self.node_hovered.emit(node_id)
        except Exception as e:
            self._handle_error("Node hover error", e)
            
    @pyqtSlot(float)
    def zoomChanged(self, scale: float):
        """Handle zoom level change from JavaScript."""
        try:
            self.logger.debug(f"Zoom changed: {scale}")
            self._current_zoom = scale
            self.zoom_changed.emit(scale)
        except Exception as e:
            self._handle_error("Zoom error", e)
            
    @pyqtSlot(int)
    def stabilizationProgress(self, progress: int):
        """Handle network stabilization progress."""
        try:
            self.logger.debug(f"Stabilization progress: {progress}%")
            self._is_stabilizing = True
            self.stabilization_progress.emit(progress)
        except Exception as e:
            self._handle_error("Stabilization progress error", e)
            
    @pyqtSlot()
    def stabilizationComplete(self):
        """Handle network stabilization completion."""
        try:
            self.logger.debug("Stabilization complete")
            self._is_stabilizing = False
            self.stabilization_complete.emit()
        except Exception as e:
            self._handle_error("Stabilization completion error", e)
            
    @pyqtSlot(str)
    def handleError(self, error_message: str):
        """Handle JavaScript errors."""
        self.logger.error(f"JavaScript error: {error_message}")
        self.error_occurred.emit(f"Visualization error: {error_message}")
        
    def _handle_error(self, context: str, error: Exception):
        """Handle errors with context."""
        message = f"{context}: {str(error)}"
        self.logger.error(message)
        self.error_occurred.emit(message)
        
    def get_current_state(self) -> Dict[str, Any]:
        """Get current network state."""
        return {
            'selected_node': self._current_node,
            'selected_nodes': list(self._selected_nodes),
            'zoom_level': self._current_zoom,
            'is_stabilizing': self._is_stabilizing
        }
        
    def reset_state(self):
        """Reset handler state."""
        self._current_node = None
        self._selected_nodes.clear()
        self._current_zoom = 1.0
        self._is_stabilizing = False
        
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Cleaning up network handler")
            self.reset_state()
            
            # Disconnect all signals
            try:
                self.node_selected.disconnect()
                self.nodes_selected.disconnect()
                self.node_hovered.disconnect()
                self.zoom_changed.disconnect()
                self.error_occurred.disconnect()
                self.stabilization_progress.disconnect()
                self.stabilization_complete.disconnect()
            except:
                pass  # Ignore disconnection errors
                
        except Exception as e:
            self.logger.error(f"Error during network handler cleanup: {e}")