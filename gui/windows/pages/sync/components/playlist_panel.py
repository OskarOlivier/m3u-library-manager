# gui/windows/pages/sync/components/playlist_panel.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from pathlib import Path
from typing import Callable, Dict, Optional
from ..state import SyncPageState, PlaylistAnalysis
from app.config import Config
import logging

class PlaylistPanel(QWidget):
    """Panel containing playlist list and controls with enhanced analysis features."""
    
    # Color constants
    SYNC_COLOR = QColor("#1E824C")  # Soft green for synced
    ERROR_COLOR = QColor("#8C1515")  # Soft red for errors
    NORMAL_COLOR = QColor("#2D2D2D")  # Default background
    REMOTE_ERROR_COLOR = QColor("#FF4444")  # Bright red for not found remotely
        
    def __init__(self, 
                 state: SyncPageState, 
                 on_analyze_all: Callable[[], None],
                 on_upload: Callable[[Path], None],
                 parent: Optional[QWidget] = None):
        """Initialize PlaylistPanel.
        
        Args:
            state: Application state manager
            on_analyze_all: Callback for analyze all action
            on_upload: Callback for upload action
            parent: Parent widget
        """
        super().__init__(parent)
        self.state = state
        self.on_analyze_all = on_analyze_all
        self.on_upload = on_upload
        self.current_playlist: Optional[Path] = None
        self.playlist_items: Dict[Path, QListWidgetItem] = {}
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.is_refreshing = False
        self.logger = logging.getLogger('playlist_panel')
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)  # Reduced spacing between elements
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title and count
        header = QHBoxLayout()
        header.setSpacing(4)
        header.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        title = QLabel("Playlists")
        title.setFont(QFont("Segoe UI", 11))
        title.setStyleSheet("color: white;")
        header.addWidget(title)
        
        # Playlist count label (right-aligned)
        self.count_label = QLabel()
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: #999999;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.count_label)
        
        layout.addLayout(header)
        
        # Playlist list with minimal styling
        self.playlist_list = QListWidget()
        self.playlist_list.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
                padding: 1px;
            }
            QListWidget::item {
                color: white;
                padding: 1px;
                border-radius: 2px;
                margin: 0px;
            }
            QListWidget::item:hover:enabled {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
        """)
        self.playlist_list.setSpacing(0)
        self.playlist_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.playlist_list)
        
        # Sync action buttons
        sync_buttons = QHBoxLayout()
        self.add_remote_btn = QPushButton("Add to Remote")
        self.delete_local_btn = QPushButton("Delete from Local")
        self.add_remote_btn.clicked.connect(self._on_add_remote)
        self.delete_local_btn.clicked.connect(self._on_delete_local)
        sync_buttons.addWidget(self.add_remote_btn)
        sync_buttons.addWidget(self.delete_local_btn)
        layout.addLayout(sync_buttons)
        
        # Analysis buttons
        analysis_buttons = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_all_btn = QPushButton("Analyze All")
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_all_btn.clicked.connect(self._on_analyze_all)
        analysis_buttons.addWidget(self.analyze_btn)
        analysis_buttons.addWidget(self.analyze_all_btn)
        layout.addLayout(analysis_buttons)
        
        # Apply button style
        button_style = """
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 4px 8px;
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
        
        for button in [self.add_remote_btn, self.delete_local_btn, 
                      self.analyze_btn, self.analyze_all_btn]:
            button.setStyleSheet(button_style)
            button.setEnabled(False)  # Initially disabled
            
    def connect_signals(self):
        """Connect to state signals."""
        self.state.analysis_completed.connect(self._on_analysis_completed)
        self.state.analysis_all_completed.connect(self._on_analysis_all_completed)
        self.state.sync_started.connect(self._on_sync_started)
        self.state.sync_completed.connect(self._on_sync_completed)
        
    def _on_selection_changed(self):
        """Handle playlist selection changes."""
        selected_items = self.playlist_list.selectedItems()
        
        if not selected_items:
            self.state.set_current_playlist(None)
            self.current_playlist = None
            self._update_button_states()
            return
            
        item = selected_items[0]
        path = Path(item.data(Qt.ItemDataRole.UserRole)['path'])
        self.current_playlist = path
        self.state.set_current_playlist(path)
        
        self._update_button_states()
        
    def _on_analyze(self):
        """Handle analyze button click."""
        if self.current_playlist:
            self.state.analysis_started.emit(self.current_playlist)
            
    def _on_analyze_all(self):
        """Handle analyze all button click."""
        self.analyze_all_btn.setEnabled(False)
        self.on_analyze_all()
        
    def _on_add_remote(self):
        """Handle add to remote button click."""
        if self.current_playlist:
            self.on_upload(self.current_playlist)
            
    def _on_delete_local(self):
        """Handle delete from local button click."""
        if self.current_playlist:
            # TODO: Implement local deletion
            pass
            
    def _update_button_states(self):
        """Update button enabled states"""
        has_selection = self.current_playlist is not None
        self.analyze_btn.setEnabled(has_selection)
        self.add_remote_btn.setEnabled(has_selection)
        self.delete_local_btn.setEnabled(has_selection)
        self.analyze_all_btn.setEnabled(True)  # Always enabled
        
        # Update sync button states based on analysis if available
        if has_selection:
            analysis = self.state.get_analysis(self.current_playlist)
            if analysis:
                self.add_remote_btn.setEnabled(not analysis.exists_remotely)
                self.delete_local_btn.setEnabled(analysis.exists_remotely)
                
    def _on_analysis_completed(self, playlist_path: Path, analysis: PlaylistAnalysis):
        """Handle completed analysis."""
        if playlist_path in self.playlist_items:
            item = self.playlist_items[playlist_path]
            self._update_item_style(item, playlist_path)
            
    def _on_analysis_all_completed(self):
        """Handle completion of bulk analysis."""
        self.analyze_all_btn.setEnabled(True)
        
    def _on_sync_started(self, operation: str):
        """Handle start of sync operation."""
        self.analyze_all_btn.setEnabled(False)
        self.add_remote_btn.setEnabled(False)
        self.delete_local_btn.setEnabled(False)
        
    def _on_sync_completed(self):
        """Handle completion of sync operation."""
        self.analyze_all_btn.setEnabled(True)
        self._update_button_states()
            
    def refresh_playlists(self):
        """Refresh the playlist list."""
        if self.is_refreshing:
            return
            
        self.is_refreshing = True
        self.playlist_list.clear()
        self.playlist_items.clear()
        
        # Get all playlists except backup and unplaylisted
        playlists = sorted(p for p in self.playlists_dir.glob("*.m3u")
                         if p.name != "Love.bak.m3u" and not p.name.startswith("Unplaylisted_"))
        
        for playlist in playlists:
            self._add_playlist_item(playlist)
            
        # Update count
        self.count_label.setText(f"{len(playlists)} playlists")
        self.is_refreshing = False
        
    def _add_playlist_item(self, playlist_path: Path):
        """Add a playlist item with appropriate styling."""
        # Create base item
        item = QListWidgetItem()
        
        # Create custom widget for content with minimal margins
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 0, 2, 0)  # Minimal margins
        layout.setSpacing(2)  # Minimal spacing
        
        # Title label
        title_label = QLabel(playlist_path.name)
        title_label.setFont(QFont("Segoe UI", 9))  # Slightly smaller font
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(title_label)
        
        # Count label (right-aligned, no stretch)
        count_label = QLabel()
        count_label.setFont(QFont("Segoe UI", 9))  # Slightly smaller font
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        count_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        layout.addWidget(count_label)
        
        # Store labels in item data
        item.setData(Qt.ItemDataRole.UserRole, {
            'path': str(playlist_path),
            'title_label': title_label,
            'count_label': count_label
        })
        
        # Set initial style
        self._update_item_style(item, playlist_path)
        
        # Set minimum size
        widget.adjustSize()
        item.setSizeHint(widget.minimumSizeHint())
        
        self.playlist_list.addItem(item)
        self.playlist_list.setItemWidget(item, widget)
        
        self.playlist_items[playlist_path] = item
        
    def _update_item_style(self, item: QListWidgetItem, playlist_path: Path):
        """Update item style based on analysis status."""
        data = item.data(Qt.ItemDataRole.UserRole)
        title_label = data['title_label']
        count_label = data['count_label']
        
        analysis = self.state.get_analysis(playlist_path)
        
        if analysis:
            if not analysis.exists_remotely:
                # Not found remotely - red with n/a
                title_label.setStyleSheet("color: #FF4444;")
                count_label.setStyleSheet("color: #FF4444;")
                count_label.setText("(n/a)")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                
            elif len(analysis.missing_remotely) == 0 and len(analysis.missing_locally) == 0:
                # Only show synced if playlist exists AND has no missing files on either side
                title_label.setStyleSheet("color: #1E824C;")
                count_label.setStyleSheet("color: #1E824C;")
                count_label.setText("(synced)")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                
            else:
                # Has differences - show counts
                title_label.setStyleSheet("color: white;")
                count_label.setStyleSheet("color: #999999;")
                remote_count = len(analysis.missing_remotely)
                local_count = len(analysis.missing_locally)
                count_label.setText(f"({remote_count},{local_count})")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
        else:
            # No analysis yet
            title_label.setStyleSheet("color: white;")
            count_label.setStyleSheet("color: #999999;")
            count_label.setText("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
            
    def cleanup(self):
        """Clean up resources."""
        self.playlist_items.clear()