# gui/windows/pages/proximity/state.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set, List
from PyQt6.QtCore import pyqtSignal
import json

from core.state.base_state import BaseState

@dataclass
class VisualizationData:
    """Stores visualization state."""
    nodes: List[Dict]
    edges: List[Dict]
    zoom_level: float = 1.0
    selected_node: Optional[str] = None

@dataclass
class ProximityStateData:
    """Serializable proximity state data."""
    visualization_data: Optional[dict] = None
    selected_playlist: Optional[str] = None
    highlighted_nodes: List[str] = None

class ProximityState(BaseState[ProximityStateData]):
    """Manages state and signals for proximity visualization."""
    
    # Visualization signals
    visualization_updated = pyqtSignal()
    visualization_error = pyqtSignal(str)
    
    # Selection signals
    node_selected = pyqtSignal(str)
    node_deselected = pyqtSignal()
    
    # Relationship signals
    relationship_strength_changed = pyqtSignal(str, float)
    
    def __init__(self):
        super().__init__()
        self.visualization_data: Optional[VisualizationData] = None
        self.selected_playlist: Optional[str] = None
        self.highlighted_nodes: List[str] = []
        self.current_zoom: float = 1.0

    async def _do_initialize(self) -> None:
        """Initialize state data."""
        await super()._do_initialize()
        self.set_status("Proximity state initialized")

    def _do_reset(self) -> None:
        """Reset state to initial values."""
        self.visualization_data = None
        self.selected_playlist = None
        self.highlighted_nodes.clear()
        self.current_zoom = 1.0

    def _get_serializable_state(self) -> dict:
        """Convert state to serializable format."""
        return {
            'visualization_data': self._serialize_visualization_data() if self.visualization_data else None,
            'selected_playlist': self.selected_playlist,
            'highlighted_nodes': self.highlighted_nodes,
            'current_zoom': self.current_zoom
        }

    def _restore_from_state(self, state_data: dict) -> None:
        """Restore state from serialized data."""
        if state_data.get('visualization_data'):
            self.visualization_data = self._deserialize_visualization_data(state_data['visualization_data'])
            self.visualization_updated.emit()
            
        self.selected_playlist = state_data.get('selected_playlist')
        self.highlighted_nodes = state_data.get('highlighted_nodes', [])
        self.current_zoom = state_data.get('current_zoom', 1.0)

        if self.selected_playlist:
            self.node_selected.emit(self.selected_playlist)

    def _serialize_visualization_data(self) -> dict:
        """Convert VisualizationData to serializable format."""
        if not self.visualization_data:
            return None
        return {
            'nodes': self.visualization_data.nodes,
            'edges': self.visualization_data.edges,
            'zoom_level': self.visualization_data.zoom_level,
            'selected_node': self.visualization_data.selected_node
        }

    def _deserialize_visualization_data(self, data: dict) -> VisualizationData:
        """Create VisualizationData from serialized data."""
        return VisualizationData(
            nodes=data['nodes'],
            edges=data['edges'],
            zoom_level=data.get('zoom_level', 1.0),
            selected_node=data.get('selected_node')
        )

    def update_visualization(self, nodes: List[Dict], edges: List[Dict]) -> None:
        """Update visualization data."""
        self.visualization_data = VisualizationData(
            nodes=nodes,
            edges=edges,
            zoom_level=self.current_zoom,
            selected_node=self.selected_playlist
        )
        self.visualization_updated.emit()

    def select_node(self, node_id: str) -> None:
        """Handle node selection."""
        self.selected_playlist = node_id
        self.node_selected.emit(node_id)

    def deselect_node(self) -> None:
        """Handle node deselection."""
        self.selected_playlist = None
        self.highlighted_nodes.clear()
        self.node_deselected.emit()

    def update_zoom(self, zoom_level: float) -> None:
        """Update current zoom level."""
        self.current_zoom = zoom_level
        if self.visualization_data:
            self.visualization_data.zoom_level = zoom_level

    def highlight_related_nodes(self, node_ids: List[str]) -> None:
        """Update highlighted nodes."""
        self.highlighted_nodes = node_ids

    def cache_current_state(self) -> bool:
        """Cache current visualization state."""
        if not self.visualization_data:
            return False
        self.save_state('proximity')
        return True

    def restore_cached_state(self) -> bool:
        """Restore cached visualization state."""
        if self.load_state('proximity'):
            if self.visualization_data:
                self.visualization_updated.emit()
            return True
        return False