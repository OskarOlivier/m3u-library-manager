# gui/windows/pages/proximity/visualization/layout_manager.py

from typing import Dict, List, Tuple, Optional
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging
from pathlib import Path

class ForceAtlas2Layout(QObject):
    """Handles force-directed layout calculations using ForceAtlas2 algorithm."""
    
    # Signals
    layout_updated = pyqtSignal(dict)  # Emits position updates as dict
    iteration_complete = pyqtSignal(int)  # Emits iteration count
    stabilized = pyqtSignal()  # Emits when layout stabilizes
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('force_atlas2')
        self.animation_timer = QTimer()
        self.animation_timer.setInterval(16)  # 60fps
        self.animation_timer.timeout.connect(self._animation_tick)
        
        # ForceAtlas2 parameters
        self.scaling = 5.0
        self.gravity = 1.0
        self.jitter_tolerance = 1.0
        self.speed_efficiency = 1.0  # Reduced for stability
        self.max_displacement = 25.0  # Reduced max movement
        self.min_distance = 30.0  # Minimum distance between nodes
        self.optimal_distance = 50.0  # Target distance between connected nodes
               
        # State tracking
        self.positions: Dict[str, np.ndarray] = {}
        self.velocities: Dict[str, np.ndarray] = {}
        self.forces: Dict[str, np.ndarray] = {}
        self.mass: Dict[str, float] = {}
        self.edges: List[Tuple[str, str, float]] = []
        
        self.iteration_count = 0
        self.is_active = False
        self.stable_threshold = 0.001
        self.global_speed = 1.0
        
    def initialize_layout(self, positions: Dict[str, np.ndarray], masses: Optional[Dict[str, float]] = None) -> None:
       """Initialize layout with starting positions and optional masses."""
       self.positions = positions.copy()
       self.velocities = {nid: np.zeros(2) for nid in positions}
       self.forces = {nid: np.zeros(2) for nid in positions}
       
       # Set masses from parameter or default to 1.0
       self.mass = masses if masses is not None else {nid: 1.0 for nid in positions}
       
       self.iteration_count = 0
       self.global_speed = 1.0  
       self.is_active = False
       
       self.layout_updated.emit(self.get_positions())
                       
    def get_positions(self) -> Dict[str, np.ndarray]:
        """Get current node positions."""
        return self.positions.copy()
        
    def calculate_iteration(self, edges: List[Tuple[str, str, float]]) -> None:
        """Calculate one iteration of ForceAtlas2 layout."""
        if not self.is_active:
            return
            
        self.edges = edges
        
        for node_id in self.forces:
            self.forces[node_id].fill(0)
            
        self._update_masses()
        self._apply_repulsion()
        self._apply_attraction()
        self._apply_gravity()
        
        total_swinging = 0.0
        total_effective_traction = 0.0
        
        for node_id in self.positions:
            force = self.forces[node_id]
            velocity = self.velocities[node_id]
            
            swinging = np.linalg.norm(force - velocity)
            total_swinging += self.mass[node_id] * swinging
            
            traction = np.linalg.norm(force + velocity)
            total_effective_traction += self.mass[node_id] * traction
            
        estimated_optimal_jitter = 0.05 * np.sqrt(len(self.positions))
        min_jitter = np.sqrt(estimated_optimal_jitter)
        target_speed = min_jitter * self.speed_efficiency * (total_effective_traction / (total_swinging + 0.1))
        
        if total_swinging / total_effective_traction > 2:
            self.global_speed *= 0.5
        else:
            self.global_speed = min(target_speed, 2.0)
            
        total_movement = 0.0
        
        for node_id in self.positions:
            force = self.forces[node_id]
            factor = self.global_speed / (1.0 + np.sqrt(np.linalg.norm(force)))
            
            displacement = force * factor
            displacement_length = np.linalg.norm(displacement)
            if displacement_length > self.max_displacement:
                displacement *= self.max_displacement / displacement_length
                
            self.positions[node_id] += displacement
            self.velocities[node_id] = displacement
            
            total_movement += displacement_length
            
        avg_movement = total_movement / len(self.positions)
        if avg_movement < self.stable_threshold:
            self.is_active = False
            self.stabilized.emit()
            
        self.iteration_count += 1
        self.layout_updated.emit(self.get_positions())
        
    def _update_masses(self) -> None:
        """Update node masses based on degree and centrality."""
        degrees = {node_id: 0 for node_id in self.positions}
        edge_weights = {node_id: 0.0 for node_id in self.positions}
        
        for source, target, weight in self.edges:
            degrees[source] += 1
            degrees[target] += 1
            edge_weights[source] += weight
            edge_weights[target] += weight
            
        max_weight = max(edge_weights.values()) if edge_weights else 1.0
        
        for node_id in self.positions:
            degree = degrees[node_id]
            weight = edge_weights[node_id]
            if degree > 0:
                # Combine degree and edge weight influence
                self.mass[node_id] = 1.0 + (weight / max_weight) * np.log1p(degree) * 0.5
            else:
                self.mass[node_id] = 1.0
            
    def _apply_repulsion(self) -> None:
        """Apply repulsive forces between all pairs of nodes."""
        nodes = list(self.positions.keys())
        
        for i, node1 in enumerate(nodes):
            pos1 = self.positions[node1]
            mass1 = self.mass[node1]
            
            for node2 in nodes[i+1:]:
                pos2 = self.positions[node2]
                diff = pos1 - pos2
                distance = np.linalg.norm(diff)
                
                if distance < 0.01:
                    diff = np.random.rand(2) * self.min_distance
                    distance = np.linalg.norm(diff)
                
                if distance < self.min_distance:
                    force = self.scaling * mass1 * self.mass[node2] * (self.min_distance / distance) ** 2
                else:
                    force = self.scaling * mass1 * self.mass[node2] / (distance ** 2)
                    
                direction = diff / distance
                force_vector = direction * force
                
                self.forces[node1] += force_vector
                self.forces[node2] -= force_vector
                
    def _apply_attraction(self) -> None:
        """Apply attractive forces along edges."""
        total_weight = sum(weight for _, _, weight in self.edges)
        if total_weight == 0:
            return
            
        attraction_scaling = 1.0 / np.sqrt(len(self.edges))
        
        for source, target, weight in self.edges:
            if source in self.positions and target in self.positions:
                pos1 = self.positions[source]
                pos2 = self.positions[target]
                diff = pos1 - pos2
                distance = np.linalg.norm(diff)
                
                if distance < 0.01 or distance < self.min_distance:
                    continue
                    
                normalized_weight = np.log1p(weight) * 0.2
                
                if distance > self.optimal_distance:
                    attraction = (distance - self.optimal_distance) * normalized_weight * attraction_scaling
                else:
                    attraction = 0
                    
                direction = diff / distance
                force = direction * attraction
                
                self.forces[source] -= force
                self.forces[target] += force
                
    def _apply_gravity(self) -> None:
        """Apply gravity force towards center."""
        center = sum(pos for pos in self.positions.values()) / len(self.positions)
        
        for node_id, pos in self.positions.items():
            diff = center - pos
            distance = np.linalg.norm(diff)
            
            if distance > 0:
                gravity_force = self.gravity * self.mass[node_id]
                self.forces[node_id] += (diff / distance) * gravity_force * (distance / 100)
                
    def scale_layout(self, scale_factor: float) -> None:
        """Scale the layout by a factor."""
        if not self.positions:
            return
            
        for node_id in self.positions:
            self.positions[node_id] *= scale_factor
            self.velocities[node_id] *= scale_factor
            
        self.layout_updated.emit(self.get_positions())
        
    def _animation_tick(self):
        if self.is_active:
            self.calculate_iteration(self.edges)

    def start(self):
        """Start layout calculations."""
        self.is_active = True
        self.animation_timer.start()
        
    def stop(self):
        """Stop layout calculations."""
        self.is_active = False
        self.animation_timer.stop()
        
    def resume(self) -> None:
        """Resume layout calculation from current state."""
        if self.positions:
            self.is_active = True
            
    def cleanup(self):
        """Clean up resources."""
        self.stop()