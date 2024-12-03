# gui/windows/pages/proximity/visualization/interaction.py

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QGraphicsSceneMouseEvent
import numpy as np
import logging
from typing import Optional, Tuple

class GraphInteractionHandler(QObject):
   """Handles mouse and keyboard interactions with the graph visualization."""

   view_panned = pyqtSignal(float, float)  # dx, dy
   view_zoomed = pyqtSignal(float)  # zoom level
   node_dragged = pyqtSignal(str, float, float)  # node_id, x, y
   
   def __init__(self):
       super().__init__()
       self.logger = logging.getLogger('graph_interaction')
       self.panning = False
       self.last_pos = None
       self.dragged_node: Optional[str] = None
       self.zoom_level = 1.0
       
   def mouse_press(self, event: QGraphicsSceneMouseEvent) -> bool:
       """Handle mouse press events."""
       if event.button() == Qt.MouseButton.LeftButton:
           self.panning = True
           self.last_pos = event.scenePos()
           return True
       return False

   def mouse_release(self, event: QGraphicsSceneMouseEvent) -> bool:
       """Handle mouse release events."""
       if event.button() == Qt.MouseButton.LeftButton:
           self.panning = False
           self.dragged_node = None
           self.last_pos = None
           return True
       return False
       
   def mouse_move(self, event: QGraphicsSceneMouseEvent) -> bool:
       """Handle mouse move events."""
       if self.panning and self.last_pos:
           current_pos = event.scenePos()
           delta = current_pos - self.last_pos
           
           if self.dragged_node:
               self.node_dragged.emit(
                   self.dragged_node, 
                   delta.x() / self.zoom_level,
                   delta.y() / self.zoom_level
               )
           else:
               self.view_panned.emit(delta.x(), delta.y())
               
           self.last_pos = current_pos
           return True
       return False
       
   def wheel(self, event) -> bool:
       """Handle mouse wheel events for zooming."""
       zoom_factor = 1.1
       if event.angleDelta().y() < 0:
           zoom_factor = 1.0 / zoom_factor
           
       self.zoom_level *= zoom_factor
       self.view_zoomed.emit(self.zoom_level)
       return True
       
   def start_node_drag(self, node_id: str):
       """Start dragging a specific node."""
       self.dragged_node = node_id
       
   def stop_node_drag(self):
       """Stop node dragging."""
       self.dragged_node = None

   def get_cursor_pos(self) -> Tuple[float, float]:
       """Get current cursor position in scene coordinates."""
       if self.last_pos:
           return self.last_pos.x(), self.last_pos.y()
       return 0.0, 0.0