# gui/windows/pages/curation/components/stats_panel.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont
import logging
from pathlib import Path
import subprocess
from datetime import datetime

from utils.m3u.parser import read_m3u, write_m3u

class StatsPanel(QWidget):
    """Panel showing library statistics and controls"""
    
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.logger = logging.getLogger('stats_panel')
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        #layout.addStretch()
        
        # Stats labels
        self.total_tracks = QLabel("Total tracks in playlists: 0")
        self.total_tracks.setFont(QFont("Segoe UI", 10))
        self.total_tracks.setStyleSheet("color: #999999;")
        
        self.unplaylisted = QLabel("Not in any playlist: 0")
        self.unplaylisted.setFont(QFont("Segoe UI", 10))
        self.unplaylisted.setStyleSheet("color: #999999;")
        
        # Collect button (properly styled and positioned)
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
        self.collect_button.clicked.connect(self._on_collect_clicked)
        
        layout.addWidget(self.total_tracks)
        layout.addWidget(self.unplaylisted)
        layout.addWidget(self.collect_button)
        
    def connect_signals(self):
        """Connect to state signals"""
        self.state.stats_updated.connect(self._on_stats_updated)
        
    def _on_stats_updated(self, total: int, unplaylisted: int):
        """Handle stats update"""
        self.total_tracks.setText(f"Total tracks in playlists: {total:,}")
        self.unplaylisted.setText(f"Not in any playlist: {unplaylisted:,}")
        
    def _on_collect_clicked(self):
        """Handle collect button click"""
        try:
            # Use playlist manager through state to handle collection
            if self.state.collect_unplaylisted():
                self.state.set_status("Created and opened new playlist")
            else:
                self.state.set_status("No unplaylisted tracks found")
        except Exception as e:
            self.logger.error(f"Error collecting unplaylisted: {e}")
            self.state.report_error("Failed to collect unplaylisted tracks")
        
    def connect_signals(self):
        """Connect to state signals"""
        self.state.stats_updated.connect(self._on_stats_updated)