# gui/windows/pages/curation/components/playlist_grid.py

from PyQt6.QtWidgets import (QWidget, QGridLayout, QScrollArea, 
                           QFrame, QVBoxLayout, QLabel, QSizePolicy,
                           QHBoxLayout)  # Added QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path
import logging
from typing import Dict

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
        
        # Title with count
        self.title_label = QLabel("Playlists (0)")
        self.title_label.setFont(QFont("Segoe UI", 11))
        self.title_label.setStyleSheet("color: white;")
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the grid UI"""
        # Create outer container and layout
        outer_container = QWidget()
        outer_layout = QVBoxLayout(outer_container)
        outer_layout.setSpacing(8)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        
        # Add title
        outer_layout.addWidget(self.title_label)
        
        # Create grid container
        grid_container = QWidget()
        self.grid = QGridLayout(grid_container)
        self.grid.setSpacing(8)
        self.grid.setContentsMargins(0, 0, 0, 0)
        
        # Add grid to scroll area
        self.setWidget(outer_container)
        outer_layout.addWidget(grid_container)
        
        # Configure scroll area
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
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
        self.state.playlist_updated.connect(self._on_playlist_updated)
        self.state.playlist_highlighted.connect(self._on_playlist_highlighted)
        self.click_handler.clicked.connect(self._on_playlist_clicked)
        
    def refresh_playlists(self, playlists_dir: Path):
        """Refresh the playlist grid"""
        # Clear existing grid
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
        self.playlist_items.clear()
        
        # Add playlists to grid
        playlists = sorted(p for p in playlists_dir.glob("*.m3u")
                          if p.name != "Love.bak.m3u")
        cols = 4
        
        for i, playlist_path in enumerate(playlists):
            try:
                track_count = len(read_m3u(str(playlist_path)))
                item = PlaylistItem(playlist_path, track_count, self.click_handler)
                self.playlist_items[playlist_path] = item
                
                row = i // cols
                col = i % cols
                self.grid.addWidget(item, row, col)
                
                # Update state
                self.state.update_playlist(playlist_path, track_count)
                
            except Exception as e:
                self.logger.error(f"Error adding playlist {playlist_path}: {e}")
        
        # Update playlist count in title
        self._update_title()
        
    def _update_title(self):
        """Update title with playlist count"""
        count = len(self.playlist_items)
        self.title_label.setText(f"Playlists ({count})")
        
    def _on_playlist_updated(self, playlist_path: Path, count: int):
        """Handle playlist track count update"""
        if playlist_path in self.playlist_items:
            self.playlist_items[playlist_path].update_display(count)
            
    def _on_playlist_highlighted(self, playlist_path: Path, highlighted: bool):
        """Handle playlist highlight state change"""
        if playlist_path in self.playlist_items:
            item = self.playlist_items[playlist_path]
            item.highlighted = highlighted
            item.update_style()
            
    def _on_playlist_clicked(self, playlist_path: Path):
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

class PlaylistItem(QWidget):
    """Interactive playlist item with separated title and count aligned to edges."""

    def __init__(self, playlist_path: Path, track_count: int, click_handler: ClickHandler = None, parent=None):
        super().__init__(parent)
        self.playlist_path = playlist_path
        self.track_count = track_count
        self.highlighted = False
        self.click_handler = click_handler

        # Ensure PlaylistItem stretches to fill available horizontal space
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.init_ui()

    def init_ui(self):
        # Create outer layout
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(0)

        # Create container widget for the entire item
        container = QWidget(self)
        outer_layout.addWidget(container)

        # Create layout for content inside container
        content_layout = QHBoxLayout(container)
        content_layout.setContentsMargins(10, 6, 10, 6)
        content_layout.setSpacing(0)

        # Title label aligned to the left
        self.title_label = QLabel(self.playlist_path.stem, container)
        self.title_label.setFont(QFont("Segoe UI", 10))
        self.title_label.setStyleSheet("color: white;")
        content_layout.addWidget(self.title_label)

        # Spacer to push count to the right
        content_layout.addStretch()

        # Count label aligned to the right
        self.count_label = QLabel(str(self.track_count), container)
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: lightgrey;")
        content_layout.addWidget(self.count_label)

        # Set cursor to pointing hand
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Apply the initial style
        self.update_style()

    def update_display(self, new_count: int = None):
        """Update the playlist display with a new count and refresh style."""
        if new_count is not None:
            self.track_count = new_count
            self.count_label.setText(str(self.track_count))
        self.update_style()

    def update_style(self):
        """Update the visual style based on highlight state."""
        # Style for the container widget (first child)
        container_style = f"""
            QWidget {{
                background-color: {"#0078D4" if self.highlighted else "#2D2D2D"};
                border-radius: 4px;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """
        self.findChild(QWidget).setStyleSheet(container_style)

    def mousePressEvent(self, event):
        """Handle click event and emit the playlist path."""
        if event.button() == Qt.MouseButton.LeftButton and self.click_handler:
            self.click_handler.clicked.emit(self.playlist_path)