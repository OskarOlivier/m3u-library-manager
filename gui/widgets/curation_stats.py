# gui/widgets/curation_stats.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from pathlib import Path

class StatsWidget(QWidget):
    """Widget for displaying library statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Create a stretch to push everything to the right
        layout.addStretch()
        
        # Stats labels
        self.total_tracks = QLabel("Total tracks: 0")
        self.total_tracks.setFont(QFont("Segoe UI", 10))
        self.total_tracks.setStyleSheet("color: #999999;")
        
        self.unplaylisted = QLabel("Loved not in playlist: 0")
        self.unplaylisted.setFont(QFont("Segoe UI", 10))
        self.unplaylisted.setStyleSheet("color: #999999;")
        
        # Collect button (renamed from "Collect Loved")
        self.collect_button = QPushButton("Collect")
        self.collect_button.setFont(QFont("Segoe UI", 10))
        self.collect_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #1982D4;
            }
            QPushButton:pressed {
                background-color: #106EBE;
            }
        """)
        
        # Add widgets to layout (after the stretch)
        layout.addWidget(self.total_tracks)
        layout.addWidget(self.unplaylisted)
        layout.addWidget(self.collect_button)
        
    def update_stats(self, total: int, unplaylisted: int):
        """Update statistics display"""
        self.total_tracks.setText(f"Total tracks: {total:,}")
        self.unplaylisted.setText(f"Loved not in playlist: {unplaylisted:,}")
        
    def enable_collect(self, enabled: bool = True):
        """Enable or disable collect button"""
        self.collect_button.setEnabled(enabled)