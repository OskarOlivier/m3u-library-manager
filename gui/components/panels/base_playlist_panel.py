# gui/components/panels/base_playlist_panel.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QListWidget, QPushButton, QFrame, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from gui.components.widgets.count_label import CountLabel
from gui.components.widgets.playlist_item import PlaylistItem
from gui.components.styles.layouts import PANEL_MARGINS, PANEL_SPACING
from gui.components.styles.fonts import TITLE_FONT, BUTTON_FONT
from gui.components.styles.colors import (
   BACKGROUND_COLOR, 
   TEXT_COLOR, 
   ITEM_HOVER,
   ITEM_SELECTED,
   SECONDARY_TEXT
)
from utils.m3u.parser import read_m3u

class BasePlaylistPanel(QWidget):
    """Base class for playlist panels with standard selection behavior."""
    
    selection_changed = pyqtSignal(object)  # Emits Path or None
    count_changed = pyqtSignal(int)  # Emits new playlist count
    
    def __init__(self, title: str = "Playlists", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.current_playlist: Optional[Path] = None
        self.playlist_items: Dict[Path, PlaylistItem] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*PANEL_MARGINS)
        layout.setSpacing(PANEL_SPACING)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(PANEL_SPACING)
        
        self.title_label = QLabel(self.title)
        self.title_label.setFont(TITLE_FONT)
        self.title_label.setStyleSheet(f"color: {TEXT_COLOR};")
        header.addWidget(self.title_label)
        
        self.count_label = CountLabel()
        header.addWidget(self.count_label)
        
        layout.addLayout(header)
        
        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.playlist_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.playlist_list.setSelectionBehavior(QListWidget.SelectionBehavior.SelectRows)
        self.playlist_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.playlist_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setup_list_style()
        layout.addWidget(self.playlist_list)
        
        # Button container
        self.button_container = QFrame()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setSpacing(PANEL_SPACING)
        layout.addWidget(self.button_container)
        
        self.setup_buttons()
        
    def setup_list_style(self):
        """Set up the playlist list styling."""
        self.playlist_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BACKGROUND_COLOR};
                border: none;
                border-radius: 4px;
                padding: 0px;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                padding: 0px;
                border-radius: 4px;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
                border: none;
            }}
            QListWidget::item:hover {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {BACKGROUND_COLOR};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #666666;
                min-height: 20px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #888888;
            }}
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, 
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
    def setup_buttons(self):
        """Override in subclasses to customize buttons."""
        pass
        
    def connect_signals(self):
        """Connect signal handlers."""
        self.playlist_list.itemSelectionChanged.connect(self._on_selection_changed)
        
    def _create_button(self, text: str, callback: Optional[callable] = None,
                     enabled: bool = True) -> QPushButton:
        """Create a styled button."""
        button = QPushButton(text)
        button.setFont(BUTTON_FONT)
        button.setEnabled(enabled)
        
        if callback:
            button.clicked.connect(callback)
            
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {ITEM_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {ITEM_SELECTED};
            }}
            QPushButton:disabled {{
                background-color: #1A1A1A;
                color: {SECONDARY_TEXT};
            }}
        """)
        
        return button
        
    def add_button(self, text: str, callback: Optional[callable] = None,
                 enabled: bool = True) -> QPushButton:
        """Add a button to the button layout."""
        button = self._create_button(text, callback, enabled)
        self.button_layout.addWidget(button)
        return button

    def _on_selection_changed(self):
        """Handle list selection change."""
        selected_items = self.playlist_list.selectedItems()
        if selected_items:
            item = selected_items[0]  # Single selection mode ensures max one item
            playlist_path = Path(item.data(Qt.ItemDataRole.UserRole))
            self._on_item_selected(playlist_path)
        else:
            self._on_item_selected(None)

    def _on_item_selected(self, playlist_path: Optional[Path]):
        """Handle standard selection (not toggling)."""
        if self.current_playlist == playlist_path:
            return
            
        # Update selection state
        if self.current_playlist in self.playlist_items:
            self.playlist_items[self.current_playlist].set_selected(False)
            
        self.current_playlist = playlist_path
        if playlist_path in self.playlist_items:
            self.playlist_items[playlist_path].set_selected(True)
            
        self.selection_changed.emit(playlist_path)
        
    def _add_playlist_item(self, playlist_path: Path):
        """Add a playlist item with standard selection behavior."""
        try:
            track_count = len(read_m3u(str(playlist_path)))
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, str(playlist_path))
            
            widget = self._create_playlist_item(playlist_path, track_count)
            widget.clicked.connect(lambda p: self._handle_item_click(item))
            
            item.setSizeHint(widget.sizeHint())
            self.playlist_list.addItem(item)
            self.playlist_list.setItemWidget(item, widget)
            self.playlist_items[playlist_path] = widget
            
        except Exception as e:
            self.logger.error(f"Error adding playlist {playlist_path}: {e}")
            
    def _handle_item_click(self, item: QListWidgetItem):
        """Handle item click by setting selection."""
        self.playlist_list.setCurrentItem(item)
            
    def _create_playlist_item(self, playlist_path: Path, track_count: int) -> PlaylistItem:
        """Create appropriate playlist item - override in subclasses."""
        return PlaylistItem(playlist_path, track_count)
        
    def refresh_playlists(self, playlists_dir: Path):
        """Refresh playlist display."""
        self.playlist_list.clear()
        self.playlist_items.clear()
        self.current_playlist = None
        
        try:
            # Get regular playlists (excluding backups and unplaylisted)
            from utils.playlist import get_regular_playlists
            playlists = get_regular_playlists(playlists_dir)
            
            # Add playlists to list
            for playlist_path in playlists:
                self._add_playlist_item(playlist_path)
                
            # Update count
            self.count_label.set_count(len(playlists), "playlists")
            self.count_changed.emit(len(playlists))
            
        except Exception as e:
            self.logger.error(f"Error refreshing playlists: {e}")
            
    def clear_selection(self):
        """Clear current selection."""
        self.playlist_list.clearSelection()
        if self.current_playlist in self.playlist_items:
            self.playlist_items[self.current_playlist].set_selected(False)
        self.current_playlist = None
        self.selection_changed.emit(None)
        
    def get_current_playlist(self) -> Optional[Path]:
        """Get currently selected playlist."""
        return self.current_playlist
        
    def keyPressEvent(self, event):
        """Handle keyboard navigation."""
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down,
                          Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
                          Qt.Key.Key_Home, Qt.Key.Key_End):
            self.playlist_list.keyPressEvent(event)
        else:
            super().keyPressEvent(event)
        
    def cleanup(self):
        """Clean up resources."""
        self.playlist_items.clear()
        self.current_playlist = None