# gui/windows/pages/curation/components/playlist_grid.py

from PyQt6.QtWidgets import (QWidget, QGridLayout, QScrollArea, 
                           QFrame, QVBoxLayout, QLabel, QSizePolicy,
                           QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Dict
import logging

from gui.widgets import PlaylistItem, ClickHandler
from utils.m3u.parser import read_m3u

class PlaylistGrid(QScrollArea):
    """Grid display of playlists with scroll support"""
                
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.playlist_items: Dict[Path, PlaylistItem] = {}
        self.click_handler = ClickHandler()
        self.logger = logging.getLogger('playlist_grid')
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the grid UI"""
        # Create outer container and layout
        outer_container = QWidget()
        outer_layout = QVBoxLayout(outer_container)
        outer_layout.setSpacing(4)  # Reduced spacing
        outer_layout.setContentsMargins(4, 4, 4, 4)  # Reduced margins
        
        # Create grid container
        grid_container = QWidget()
        grid_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.grid = QGridLayout(grid_container)
        self.grid.setSpacing(4)  # Reduced grid spacing
        self.grid.setContentsMargins(0, 0, 0, 0)
        
        # Add grid to outer layout
        outer_layout.addWidget(grid_container)
        
        # Configure scroll area
        self.setWidget(outer_container)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 16px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                min-height: 20px;
                border-radius: 3px;
                margin: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7F7F7F;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
    def connect_signals(self):
        """Connect to state signals"""
        self.state.playlist_updated.connect(self.on_playlist_updated)
        self.state.playlist_highlighted.connect(self.on_playlist_highlighted)
        self.click_handler.clicked.connect(self.on_playlist_clicked)
        
    def refresh_playlists(self, playlists_dir: Path):
        """Refresh the playlist grid"""
        # Clear existing grid
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
        self.playlist_items.clear()
        
        # Get regular playlists
        from utils.playlist.stats import get_regular_playlists
        playlists = get_regular_playlists(playlists_dir)
        
        cols = 4
        
        try:
            for i, playlist_path in enumerate(playlists):
                self.logger.debug(f"Adding playlist: {playlist_path}")
                try:
                    track_count = len(read_m3u(str(playlist_path)))
                    item = PlaylistItem(playlist_path, track_count, self.click_handler)
                    self.playlist_items[playlist_path] = item
                    
                    row = i // cols
                    col = i % cols
                    self.logger.debug(f"Adding to grid at position ({row}, {col})")
                    self.grid.addWidget(item, row, col)
                    
                    # Update state
                    self.state.update_playlist(playlist_path, track_count)
                    
                except Exception as e:
                    self.logger.error(f"Error adding playlist {playlist_path}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error refreshing playlists: {e}", exc_info=True)
            
    def on_playlist_updated(self, playlist_path: Path, count: int):
        """Handle playlist track count update"""
        if playlist_path in self.playlist_items:
            self.playlist_items[playlist_path].update_display(count)
            
    def on_playlist_highlighted(self, playlist_path: Path, highlighted: bool):
        """Handle playlist highlight state change"""
        if playlist_path in self.playlist_items:
            item = self.playlist_items[playlist_path]
            item.highlighted = highlighted
            item.update_style()
            
    def on_playlist_clicked(self, playlist_path: Path):
        """Handle playlist click"""
        if not self.state.current_song:
            return
            
        item = self.playlist_items[playlist_path]
        new_state = not item.highlighted
        
        # Show status
        operation = "removing from" if item.highlighted else "adding to"
        self.state.set_status(f"{operation} {playlist_path.name}...")
        
        # Emit through state
        self.state.emit_playlist_clicked(playlist_path)