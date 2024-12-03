from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen, QColor
import pyqtgraph as pg
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional, Set, Tuple

from .layout_manager import ForceAtlas2Layout

class PlaylistGraphWidget(QWidget):
    """PyQtGraph-based playlist relationship visualization widget."""
    
    node_selected = pyqtSignal(str)  # Node ID
    node_hovered = pyqtSignal(str)   # Node ID 
    layout_stabilized = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('playlist_graph')
        self.logger.setLevel(logging.DEBUG)
        
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Tuple[str, str, float]] = []
        self.isolated_nodes: Set[str] = set()
        
        self.edge_lines: Dict[Tuple[str, str], pg.PlotCurveItem] = {}
        self.node_labels: Dict[str, pg.TextItem] = {}
        
        self.selected_node: Optional[str] = None
        self.hovered_node: Optional[str] = None
        self.connected_nodes: Set[str] = set()
        self.connected_edges: Set[Tuple[str, str]] = set()
        
        self.layout_engine = ForceAtlas2Layout()
        
        self.setup_ui()
        self.setup_graph()
        self._connect_layout_signals()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#202020')
        layout.addWidget(self.plot_widget)
        
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.hideAxis('left')
        self.plot_item.hideAxis('bottom')
        self.plot_widget.setAntialiasing(True)
        
    def setup_graph(self):
        self.node_plot = pg.ScatterPlotItem(
            size=30,
            symbol='o',
            brush=pg.mkBrush('#404040'),
            pen=pg.mkPen('#1E1E1E', width=2),
            hoverable=True,
            z=10
        )
        self.plot_item.addItem(self.node_plot)
        
        self.node_plot.sigClicked.connect(self._on_node_clicked)
        self.node_plot.sigHovered.connect(self._on_node_hovered)
        
    def _connect_layout_signals(self):
        self.layout_engine.layout_updated.connect(self.update_positions)
        self.layout_engine.stabilized.connect(self._on_layout_stabilized)
        
    def update_graph(self, nodes_data: List[Dict], edges_data: List[Dict]):
        self.logger.info(f"Updating graph with {len(nodes_data)} nodes and {len(edges_data)} edges")
        
        self._clear_graph()
        
        connected_nodes = set()
        for edge in edges_data:
            connected_nodes.add(edge['from'])
            connected_nodes.add(edge['to'])
            
        track_counts = [node.get('value', 1) for node in nodes_data]
        min_tracks = min(track_counts)
        max_tracks = max(track_counts)
        track_range = max_tracks - min_tracks
                     
        positions = {}
        for node in nodes_data:
            node_id = node['id']
            if node_id not in connected_nodes:
                self.isolated_nodes.add(node_id)
                continue

            tracks = node.get('value', 1)
            normalized_tracks = (tracks - min_tracks) / track_range if track_range > 0 else 0.5
            
            # Scale radius inversely with track count - larger playlists start closer to center
            base_radius = 400 * (1 - normalized_tracks) + 100
            angle = np.random.uniform(0, 2 * np.pi)
            
            pos = np.array([
                base_radius * np.cos(angle),
                base_radius * np.sin(angle)
            ])
            
            # Scale node size with sqrt of track count for better visual balance
            base_size = 20
            size_scale = 3
            size = base_size + size_scale * np.sqrt(normalized_tracks * 100)
            
            self.nodes[node_id] = {
                'label': node['label'],
                'value': tracks,
                'pos': pos,
                'size': size,
                'mass': 1 + normalized_tracks  # Larger playlists have more mass
            }
            positions[node_id] = pos
            
            label = pg.TextItem(
                text=node['label'],
                color=(255, 255, 255),
                anchor=(0.5, -0.25)
            )
            label.setPos(pos[0], pos[1])
            self.plot_item.addItem(label)
            self.node_labels[node_id] = label
            
        for edge in edges_data:
            source = edge['from']
            target = edge['to']
            strength = edge.get('value', 1.0)
            
            if source not in self.isolated_nodes and target not in self.isolated_nodes:
                self.edges.append((source, target, strength))
                
        self.layout_engine.initialize_layout(positions, {
            node_id: data['mass'] 
            for node_id, data in self.nodes.items()
        })
        
        self.update_positions(positions)
        self.layout_engine.start()
        
    def update_positions(self, positions: Dict[str, np.ndarray]):
        if not self.nodes:
            return
            
        self._update_edges()
        
        node_spots = []
        for node_id, pos in positions.items():
            if node_id in self.nodes and node_id not in self.isolated_nodes:
                self.nodes[node_id]['pos'] = pos
                opacity = self._get_node_opacity(node_id)
                
                node_spots.append({
                    'pos': pos,
                    'data': node_id,
                    'size': self.nodes[node_id].get('size', 30),
                    'symbol': 'o',
                    'brush': self._get_node_brush(node_id, opacity)
                })
                
        self.node_plot.setData(node_spots)
        
        for node_id, label in self.node_labels.items():
            if node_id in self.nodes and node_id not in self.isolated_nodes:
                pos = self.nodes[node_id]['pos']
                label.setPos(pos[0], pos[1])
                label.setOpacity(self._get_node_opacity(node_id))
                
    def _update_edges(self):
        for source, target, strength in self.edges:
            edge_key = (source, target)
            source_pos = self.nodes[source]['pos']
            target_pos = self.nodes[target]['pos']
            
            if edge_key not in self.edge_lines:
                line = pg.PlotCurveItem(
                    pen=self._get_edge_pen(edge_key),
                    z=0
                )
                self.plot_item.addItem(line)
                self.edge_lines[edge_key] = line
                
            line = self.edge_lines[edge_key]
            line.setData(
                x=[source_pos[0], target_pos[0]],
                y=[source_pos[1], target_pos[1]]
            )
            line.setPen(self._get_edge_pen(edge_key))
            
    def _get_node_brush(self, node_id: str, opacity: float = 1.0) -> pg.mkBrush:
        if node_id == self.selected_node:
            color = QColor(0, 212, 120)
        elif node_id in self.connected_nodes:
            color = QColor(0, 120, 212)
        else:
            color = QColor(64, 64, 64)
            
        color.setAlphaF(opacity)
        return pg.mkBrush(color)
        
    def _get_edge_pen(self, edge_key: Tuple[str, str]) -> QPen:
        if edge_key in self.connected_edges:
            color = QColor(0, 120, 212)
            width = 2
        else:
            color = QColor(255, 255, 255)
            width = 1
            
        opacity = 1.0 if not self.hovered_node or edge_key in self.connected_edges else 0.5
        color.setAlphaF(opacity)
        
        return QPen(color, width)
        
    def _get_node_opacity(self, node_id: str) -> float:
        if not self.hovered_node:
            return 1.0
        return 1.0 if node_id == self.hovered_node or node_id in self.connected_nodes else 0.5
        
    def _on_node_clicked(self, plot, points):
        if len(points) == 0:
            return
            
        node_id = points[0].data()
        if node_id == self.selected_node:
            self._clear_selection()
        else:
            self._select_node(node_id)
            
    def _on_node_hovered(self, plot, points):
        if len(points) == 0:
            self._clear_hover()
            return
            
        node_id = points[0].data()
        self._set_hover_state(node_id)
        
    def _set_hover_state(self, node_id: str):
        if node_id == self.hovered_node:
            return
            
        self.hovered_node = node_id
        self.connected_nodes = self._get_connected_nodes(node_id)
        self.connected_edges = self._get_connected_edges(node_id)
        
        self.update_positions(self._get_current_positions())
        self.node_hovered.emit(node_id)
        
    def _clear_hover(self):
        if not self.hovered_node:
            return
            
        self.hovered_node = None
        self.connected_nodes.clear()
        self.connected_edges.clear()
        
        self.update_positions(self._get_current_positions())
        
    def _select_node(self, node_id: str):
        self.selected_node = node_id
        self.update_positions(self._get_current_positions())
        self.node_selected.emit(node_id)
        
    def _clear_selection(self):
        self.selected_node = None
        self.update_positions(self._get_current_positions())
        self.node_selected.emit('')
        
    def _get_connected_nodes(self, node_id: str) -> Set[str]:
        connected = set()
        for source, target, _ in self.edges:
            if source == node_id:
                connected.add(target)
            elif target == node_id:
                connected.add(source)
        return connected
        
    def _get_connected_edges(self, node_id: str) -> Set[Tuple[str, str]]:
        connected = set()
        for source, target, _ in self.edges:
            if source == node_id or target == node_id:
                connected.add((source, target))
        return connected
        
    def _get_current_positions(self) -> Dict[str, np.ndarray]:
        return self.layout_engine.get_positions()
        
    def _clear_graph(self):
        self.nodes.clear()
        self.edges.clear()
        self.isolated_nodes.clear()
        
        for line in self.edge_lines.values():
            self.plot_item.removeItem(line)
        self.edge_lines.clear()
        
        for label in self.node_labels.values():
            self.plot_item.removeItem(label)
        self.node_labels.clear()
        
        self.selected_node = None
        self.hovered_node = None
        self.connected_nodes.clear()
        self.connected_edges.clear()
        
    def _on_layout_stabilized(self):
        self.layout_stabilized.emit()
        
    def cleanup(self):
        self.layout_engine.stop()
        self._clear_graph()
        if hasattr(self, 'node_plot'):
            self.plot_item.removeItem(self.node_plot)