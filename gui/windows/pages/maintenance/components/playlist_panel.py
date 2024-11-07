# gui/windows/pages/maintenance/components/playlist_panel.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Optional

class PlaylistPanel(QWidget):
    """Panel for playlist selection and management"""
    
    playlistSelected = pyqtSignal(Path)
    playlistAnalyzed = pyqtSignal(Path)
    playlistDeleted = pyqtSignal(Path)
    
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.current_playlist: Optional[Path] = None
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the panel UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title and count
        header = QHBoxLayout()
        
        title = QLabel("Playlists")
        title.setFont(QFont("Segoe UI", 11))
        title.setStyleSheet("color: white;")
        header.addWidget(title)
        
        self.count_label = QLabel("0 playlists")
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: #999999;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.count_label)
        
        layout.addLayout(header)
        
        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
                padding: 4px;
            }
            QListWidget::item {
                color: white;
                padding: 6px;
                margin: 2px;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
        """)
        self.playlist_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.playlist_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)
        self.analyze_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.delete_btn.setEnabled(False)
        
        for btn in [self.analyze_btn, self.delete_btn]:
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    color: white;
                    border: none;
                    border-radius: 2px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
                QPushButton:pressed {
                    background-color: #505050;
                }
                QPushButton:disabled {
                    background-color: #1A1A1A;
                    color: #666666;
                }
            """)
            button_layout.addWidget(btn)
            
        layout.addLayout(button_layout)
        
    def refresh_playlists(self, playlists_dir: Path):
        """Refresh the playlist list"""
        self.playlist_list.clear()
        
        playlists = sorted(p for p in playlists_dir.glob("*.m3u")
                          if p.name != "Love.bak.m3u")
                          
        for playlist in playlists:
            item = QListWidgetItem(playlist.name)
            item.setData(Qt.ItemDataRole.UserRole, str(playlist))
            self.playlist_list.addItem(item)
            
        self.count_label.setText(f"{len(playlists)} playlists")
        self._update_button_states()
        
    def on_selection_changed(self):
        """Handle playlist selection changes"""
        items = self.playlist_list.selectedItems()
        if items:
            self.current_playlist = Path(items[0].data(Qt.ItemDataRole.UserRole))
            self.playlistSelected.emit(self.current_playlist)
        else:
            self.current_playlist = None
            
        self._update_button_states()
        
    def on_analyze_clicked(self):
        """Handle analyze button click"""
        if self.current_playlist:
            self.playlistAnalyzed.emit(self.current_playlist)
            
    def on_delete_clicked(self):
        """Handle delete button click"""
        if self.current_playlist:
            self.playlistDeleted.emit(self.current_playlist)
            
    def _update_button_states(self):
        """Update button enabled states"""
        has_selection = self.current_playlist is not None
        self.analyze_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
    def connect_signals(self):
        """Connect to state signals"""
        # Connect to delete completion signal
        self.state.delete_completed.connect(self.on_delete_completed)
        
    def on_delete_completed(self):
        """Handle successful playlist deletion"""
        if self.current_playlist:
            # Find and remove the item for the deleted playlist
            for i in range(self.playlist_list.count()):
                item = self.playlist_list.item(i)
                if Path(item.data(Qt.ItemDataRole.UserRole)) == self.current_playlist:
                    self.playlist_list.takeItem(i)
                    break
                    
            # Update count
            count = self.playlist_list.count()
            self.count_label.setText(f"{count} playlists")
            
            # Clear current selection
            self.current_playlist = None
            self._update_button_states()

    def remove_playlist(self, playlist_path: Path):
        """Remove a playlist from the list"""
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            if Path(item.data(Qt.ItemDataRole.UserRole)) == playlist_path:
                self.playlist_list.takeItem(i)
                break
                
        # Update count
        count = self.playlist_list.count()
        self.count_label.setText(f"{count} playlists")