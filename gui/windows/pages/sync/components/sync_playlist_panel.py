# gui/windows/pages/sync/components/sync_playlist_panel.py

from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import Optional
import logging

from gui.components.panels.base_playlist_panel import BasePlaylistPanel
from utils.m3u.parser import read_m3u
from utils.playlist.stats import get_regular_playlists
from .sync_playlist_item import SyncPlaylistItem

class PlaylistPanel(BasePlaylistPanel):
    """Sync playlist panel with sync state visualization."""
    
    analyze_requested = pyqtSignal(Path)
    analyze_all_requested = pyqtSignal()
    upload_requested = pyqtSignal(Path)
    
    def __init__(self, state, on_analyze_all, on_upload, parent=None):
        self.state = state
        self.on_analyze_all = on_analyze_all
        self.on_upload = on_upload
        super().__init__(title="Playlists", parent=parent)
        
    def setup_buttons(self):
        """Set up sync-specific buttons."""
        self.analyze_btn = self.add_button(
            "Analyze",
            lambda: self._on_analyze_clicked(),
            enabled=False
        )
        
        self.analyze_all_btn = self.add_button(
            "Analyze All",
            self.on_analyze_all
        )
        
        self.upload_btn = self.add_button(
            "Upload",
            lambda: self._on_upload_clicked(),
            enabled=False
        )
        
    def connect_signals(self):
        """Connect signal handlers."""
        super().connect_signals()
        
        # Connect selection change to button state updates
        def update_button_states(playlist_path):
            enabled = playlist_path is not None
            self.analyze_btn.setEnabled(enabled)
            
        self.selection_changed.connect(update_button_states)
        
        # Connect to state signals
        if hasattr(self.state, 'analysis_completed'):
            self.state.analysis_completed.connect(self.update_playlist)
        
    def _create_playlist_item(self, playlist_path: Path, track_count: int) -> SyncPlaylistItem:
        """Create sync-specific playlist item."""
        return SyncPlaylistItem(playlist_path, track_count)
        
    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        if self.current_playlist:
            self.analyze_requested.emit(self.current_playlist)
            
    def _on_upload_clicked(self):
        """Handle upload button click."""
        if self.current_playlist and self.on_upload:
            self.on_upload(self.current_playlist)
            
    def update_playlist(self, playlist_path: Path, analysis):
        """Update playlist display with sync analysis."""
        if playlist_path in self.playlist_items:
            widget = self.playlist_items[playlist_path]
            widget.set_sync_state(
                exists_remotely=analysis.exists_remotely,
                missing_remotely=len(analysis.missing_remotely),
                missing_locally=len(analysis.missing_locally)
            )
            
            # Update upload button if this is the current playlist
            if playlist_path == self.current_playlist:
                self.upload_btn.setEnabled(self.state.is_playlist_uploadable(playlist_path))

    def _on_playlist_selected(self, playlist_path: Path):
        """Handle playlist selection."""
        super()._on_playlist_selected(playlist_path)
        
        self.upload_btn.setEnabled(False)
        
        # Update upload button based on analysis state
        self.upload_btn.setEnabled(self.state.is_playlist_uploadable(playlist_path))
                
    def _update_button_states(self, playlist_path: Optional[Path] = None):
        """Update button enabled states based on selection and analysis."""
        enabled = playlist_path is not None
        self.analyze_btn.setEnabled(enabled)
        
        # Update upload button based on analysis
        if enabled and playlist_path:
            analysis = self.state.get_analysis(playlist_path)
            self.upload_btn.setEnabled(
                analysis is not None and not analysis.exists_remotely
            )
        else:
            self.upload_btn.setEnabled(False)
            
    def refresh_playlists(self, playlists_dir: Path):
        """Refresh the playlist list."""
        self.playlist_list.clear()
        self.playlist_items.clear()
        
        # Get regular playlists
        playlists = get_regular_playlists(playlists_dir)
        
        # Add playlists to list with cached analysis state
        for playlist_path in playlists:
            try:
                track_count = len(read_m3u(str(playlist_path)))
                
                # Create list item
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, str(playlist_path))
                
                # Create and set specialized sync item
                widget = SyncPlaylistItem(playlist_path, track_count)
                widget.clicked.connect(lambda p: self.selection_changed.emit(p))
                item.setSizeHint(widget.sizeHint())
                
                # Apply cached analysis state if available
                analysis = self.state.get_analysis(playlist_path)
                if analysis:
                    widget.set_sync_state(
                        exists_remotely=analysis.exists_remotely,
                        missing_remotely=len(analysis.missing_remotely),
                        missing_locally=len(analysis.missing_locally)
                    )
                
                self.playlist_list.addItem(item)
                self.playlist_list.setItemWidget(item, widget)
                self.playlist_items[playlist_path] = widget
                
            except Exception as e:
                self.logger.error(f"Error adding playlist {playlist_path}: {e}")
                
        # Update count
        self.count_label.set_count(len(playlists), "playlists")
        self.count_changed.emit(len(playlists))