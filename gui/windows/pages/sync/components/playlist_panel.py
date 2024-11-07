# gui/windows/pages/sync/components/playlist_panel.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from pathlib import Path
from typing import Callable, Dict

from ..state import SyncPageState, PlaylistAnalysis
from app.config import Config

class PlaylistPanel(QWidget):
    """Panel containing playlist list and controls."""
    
    # Color constants
    SYNC_COLOR = QColor("#1E824C")  # Soft green
    ERROR_COLOR = QColor("#8C1515")  # Soft red
    NORMAL_COLOR = QColor("#2D2D2D")  # Default background
    REMOTE_ERROR_COLOR = QColor("#FF4444")  # Bright red for not found remotely
    
    def __init__(self, state: SyncPageState, 
                 on_analyze: Callable[[Path], None],
                 on_analyze_all: Callable[[], None]):
        super().__init__()
        self.state = state
        self.on_analyze = on_analyze
        self.on_analyze_all = on_analyze_all
        self.playlist_items: Dict[Path, QListWidgetItem] = {}
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title and controls
        header = QHBoxLayout()
        
        # Title label
        title = QLabel("Playlists")
        title.setFont(QFont("Segoe UI", 11))
        title.setStyleSheet("color: white;")
        header.addWidget(title)
        
        # Analyze All button
        self.analyze_all_btn = QPushButton("Analyze All")
        self.analyze_all_btn.clicked.connect(self.on_analyze_all)
        header.addWidget(self.analyze_all_btn)
        
        # Playlist count label
        self.count_label = QLabel()
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
            }
            QListWidget::item {
                color: white;
                padding: 8px;
                border-radius: 2px;
            }
            QListWidget::item:hover:enabled {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
            QListWidget::item:disabled {
                color: #CCCCCC;
            }
        """)
        self.playlist_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.playlist_list)
        
        # Analyze button
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)
        
        # Apply button style
        button_style = """
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
                font-family: 'Segoe UI';
                font-size: 11pt;
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
        """
        self.analyze_btn.setStyleSheet(button_style)
        self.analyze_all_btn.setStyleSheet(button_style)
        
    def _apply_analysis_style(self, item: QListWidgetItem, analysis: PlaylistAnalysis):
        """Apply styling based on analysis results."""
        if not analysis.exists_remotely:
            # Playlist not found remotely - show in red and disable
            item.setBackground(self.REMOTE_ERROR_COLOR)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            item.setToolTip("Playlist not found on remote system")
        elif analysis.is_synced:
            # Fully synced - show in green and disable
            item.setBackground(self.SYNC_COLOR)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            item.setToolTip("Playlist is fully synchronized")
        else:
            # Has differences - show counts
            item.setBackground(self.NORMAL_COLOR)
            remote_count = len(analysis.missing_remotely)
            local_count = len(analysis.missing_locally)
            item.setText(f"{item.text()} ({remote_count}, {local_count})")
            item.setToolTip(f"Missing remotely: {remote_count}\nMissing locally: {local_count}")
            
    def connect_signals(self):
        """Connect state signals."""
        self.state.analysis_completed.connect(self.on_analysis_completed)
        self.state.analysis_all_completed.connect(self.refresh_playlists)
        
    def refresh_playlists(self):
        """Load playlists into list."""
        self.playlist_list.clear()
        self.playlist_items.clear()
        
        # Get all playlists except backup
        playlists = sorted(p for p in self.playlists_dir.glob("*.m3u")
                         if p.name != "Love.bak.m3u")
        
        for playlist in playlists:
            self.add_playlist_item(playlist)
            
        # Update count
        self.count_label.setText(f"{len(playlists)} playlists")
        
    def add_playlist_item(self, playlist_path: Path):
        """Add a playlist item with appropriate styling."""
        item = QListWidgetItem(playlist_path.name)
        item.setData(Qt.ItemDataRole.UserRole, str(playlist_path))
        
        # Check for existing analysis
        analysis = self.state.get_analysis(playlist_path)
        if analysis:
            self._apply_analysis_style(item, analysis)
        else:
            item.setBackground(self.NORMAL_COLOR)
            
        self.playlist_list.addItem(item)
        self.playlist_items[playlist_path] = item
        
    def on_selection_changed(self):
        """Handle playlist selection changes."""
        selected_items = self.playlist_list.selectedItems()
        
        if not selected_items:
            self.state.set_current_playlist(None)
            self.analyze_btn.setEnabled(False)
            return
            
        item = selected_items[0]
        if not item.flags() & Qt.ItemFlag.ItemIsEnabled:
            self.playlist_list.clearSelection()
            self.state.set_current_playlist(None)
            self.analyze_btn.setEnabled(False)
            return
            
        playlist_path = Path(item.data(Qt.ItemDataRole.UserRole))
        self.state.set_current_playlist(playlist_path)
        self.analyze_btn.setEnabled(True)
            
    def on_analyze_clicked(self):
        """Handle analyze button click."""
        if self.state.current_playlist:
            self.on_analyze(self.state.current_playlist)
            
    def on_analysis_completed(self, playlist_path: Path, analysis: PlaylistAnalysis):
        """Handle completed analysis."""
        if playlist_path in self.playlist_items:
            item = self.playlist_items[playlist_path]
            self._apply_analysis_style(item, analysis)