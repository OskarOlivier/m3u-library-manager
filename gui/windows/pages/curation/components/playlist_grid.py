# gui/windows/pages/curation/components/playlist_grid.py

from PyQt6.QtWidgets import (QScrollArea, QWidget, QGridLayout, 
                          QVBoxLayout, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import Dict, Set
import logging

from utils.m3u.parser import read_m3u
from core.matching.song_matcher import SongMatchResult
from .curation_playlist_item import CurationPlaylistItem

class PlaylistGrid(QScrollArea):
    """Grid display of playlists with toggle selection functionality."""
    
    # Signals
    playlist_clicked = pyqtSignal(Path)  # Emits playlist path when clicked
    playlist_toggled = pyqtSignal(Path, bool)  # Emits (path, new_state) when toggled
    selection_changed = pyqtSignal()  # Emits when selection state changes
    
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.playlist_items: Dict[Path, CurationPlaylistItem] = {}
        
        # Set up logger explicitly
        self.logger = logging.getLogger('playlist_grid')
        self.logger.setLevel(logging.DEBUG)
        
        # Ensure handler is added
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
                   
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                min-height: 20px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #888888;
            }
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, 
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the grid UI."""
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(4)
        self.grid.setContentsMargins(0, 0, 0, 0)
        
        self.setWidget(self.container)
               
    def connect_signals(self):
        """Connect signal handlers."""
        
        # State signals with verification
        self.state.song_changed.connect(self._on_song_changed)
        self.state.song_cleared.connect(self._clear_selection)
        self.state.playlist_updated.connect(self._on_playlist_updated)
        
        # Critical selection signals
        self.state.playlist_selected.connect(self._on_playlist_selected)
        self.state.playlist_selection_changed.connect(self._on_selection_set_changed)
        
    def refresh_playlists(self, playlists_dir: Path):
        """Refresh the playlist grid."""
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.playlist_items.clear()
        
        try:
            from utils.playlist.stats import get_regular_playlists
            playlists = get_regular_playlists(playlists_dir)
            grid_width = 5
            
            for i, playlist_path in enumerate(playlists):
                row = i // grid_width
                col = i % grid_width
                
                track_count = len(read_m3u(str(playlist_path)))
                item = CurationPlaylistItem(playlist_path, track_count)
                item.clicked.connect(self._on_item_clicked)
                item.setMinimumWidth(160)
                
                # Set initial selection state if in state's selected playlists
                if playlist_path in self.state.selected_playlists:
                    self.logger.debug(f"Setting initial selection for {playlist_path.name}")
                    item.set_selected(True)
                
                self.grid.addWidget(item, row, col)
                self.playlist_items[playlist_path] = item
                
            if playlists:
                last_row = (len(playlists) - 1) // grid_width + 1
                self.grid.setRowStretch(last_row, 1)
           
        except Exception as e:
            self.logger.error(f"Error refreshing playlists: {e}", exc_info=True)

    def _on_item_clicked(self, playlist_path: Path):
        """Handle playlist item click."""
        if not self.state.current_song:
            return
        
        # Let state handle the toggle
        was_selected = playlist_path in self.state.selected_playlists
        
        # Emit signals for state management
        self.playlist_clicked.emit(playlist_path)
        self.playlist_toggled.emit(playlist_path, not was_selected)
        self.selection_changed.emit()

    def _on_song_changed(self, song_info: SongMatchResult):
        """Handle song change with match results."""
        
        # REMOVE THIS LINE - Don't clear selections here as state will handle it
        # self._clear_selection()
        
        # State will handle playlist matching and selection updates
        # We just need to make sure our visual state matches
        if self.state.current_file:
            self._update_selections_from_state()
            matching_playlists = len(self.state.selected_playlists)
            self.state.set_status(f"Song found in {matching_playlists} playlists")
                    
    def _on_playlist_selected(self, playlist_path: Path, selected: bool):
        """Handle individual playlist selection state change."""
        if playlist_path in self.playlist_items:
            item = self.playlist_items[playlist_path]
            item.set_selected(selected)

    def _on_selection_set_changed(self, selected_playlists: Set[Path]):
        """Handle bulk selection state changes."""
        
        # Update all items to match the new selection set
        for playlist_path, item in self.playlist_items.items():
            selected = playlist_path in selected_playlists
            item.set_selected(selected)
                
    def _on_playlist_updated(self, playlist_path: Path, count: int):
        """Handle playlist track count update."""
        if playlist_path in self.playlist_items:
            item = self.playlist_items[playlist_path]
            item.update_count(count)
       
    def _clear_selection(self):
        """Clear all playlist selections."""
        self.state.clear_playlist_selections()  # Clear state first
        # UI will update through state signals

    def _update_selections_from_state(self):
        """Update visual selection state to match current state."""
        for playlist_path, item in self.playlist_items.items():
            selected = playlist_path in self.state.selected_playlists
            item.set_selected(selected)
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Cleaning up playlist grid")
            
            # Disconnect signals
            try:
                if hasattr(self, 'state'):
                    self.state.song_changed.disconnect()
                    self.state.song_cleared.disconnect()
                    self.state.playlist_updated.disconnect()
                    self.state.playlist_selected.disconnect()
                    self.state.playlist_selection_changed.disconnect()
            except Exception as e:
                self.logger.debug(f"Error disconnecting signals: {e}")

            # Clean up playlist items
            while self.grid.count():
                item = self.grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.playlist_items.clear()
            
            # Clean up container
            if hasattr(self, 'container'):
                self.container.deleteLater()
                self.container = None

        except Exception as e:
            self.logger.error(f"Error during playlist grid cleanup: {e}")