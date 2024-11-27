# gui/windows/pages/maintenance/components/maintenance_playlist_panel.py

from PyQt6.QtWidgets import (QListWidgetItem, QWidget, 
                           QVBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
import logging

from gui.components.panels.base_playlist_panel import BasePlaylistPanel
from utils.m3u.parser import read_m3u
from utils.playlist.stats import get_regular_playlists
from .maintenance_playlist_item import MaintenancePlaylistItem

class PlaylistPanel(BasePlaylistPanel):
    """Maintenance playlist panel with sync-matching selection behavior."""
    
    analyze_requested = pyqtSignal(Path)
    analyze_all_requested = pyqtSignal()
    repair_requested = pyqtSignal(Path)
    delete_requested = pyqtSignal(Path)
    
    def __init__(self, state, parent=None):
        self.state = state
        super().__init__(title="Playlists", parent=parent)
        
    def _create_playlist_item(self, playlist_path: Path, track_count: int) -> MaintenancePlaylistItem:
        """Create maintenance-specific playlist item."""
        return MaintenancePlaylistItem(playlist_path, track_count)

    def _on_playlist_selected(self, playlist_path: Path):
        """Handle playlist selection."""
        super()._on_playlist_selected(playlist_path)
        
        # Update button states based on analysis state
        analysis = self.state.get_analysis(playlist_path) if playlist_path else None
        self.repair_btn.setEnabled(bool(analysis and analysis.has_errors()))

    def setup_buttons(self):
        """Set up maintenance-specific buttons."""
        self.analyze_btn = self.add_button(
            "Analyze",
            lambda: self._on_analyze_clicked(),
            enabled=False
        )
        
        self.analyze_all_btn = self.add_button(
            "Analyze All",
            lambda: self.analyze_all_requested.emit()
        )
        
        self.repair_btn = self.add_button(
            "Repair",
            lambda: self._on_repair_clicked(),
            enabled=False
        )
        
        self.delete_btn = self.add_button(
            "Delete",
            lambda: self._on_delete_clicked(),
            enabled=False
        )

    def update_playlist(self, playlist_path: Path, analysis):
        """Update playlist display with analysis results."""
        if playlist_path in self.playlist_items:
            widget = self.playlist_items[playlist_path]
            
            details = []
            if not analysis.exists_remotely:
                details.append("Not found remotely")
            if analysis.missing_files:
                details.append(f"{len(analysis.missing_files)} missing files")
            if analysis.has_duplicates:
                details.append("Has duplicates")
                
            widget.set_analysis_state(
                exists_remotely=analysis.exists_remotely,
                has_errors=len(analysis.missing_files) > 0,
                has_warnings=analysis.has_duplicates,
                details=" | ".join(details) if details else None
            )
            
            # Update repair button if this is the current playlist
            if playlist_path == self.current_playlist:
                self.repair_btn.setEnabled(analysis.has_errors())

    def connect_signals(self):
        """Connect signal handlers."""
        super().connect_signals()
        
        # Connect to state signals
        if hasattr(self.state, 'analysis_completed'):
            self.state.analysis_completed.connect(self.update_playlist)

    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        if self.current_playlist:
            self.analyze_requested.emit(self.current_playlist)
            
    def _on_repair_clicked(self):
        """Handle repair button click."""
        if self.current_playlist:
            self.repair_requested.emit(self.current_playlist)
            
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self.current_playlist:
            self.delete_requested.emit(self.current_playlist)
        
    def refresh_playlists(self, playlists_dir: Path):
        """Refresh the playlist list."""
        self.playlist_list.clear()
        self.playlist_items.clear()
        
        # Get regular playlists
        playlists = get_regular_playlists(playlists_dir)
        
        # Add playlists to list
        for playlist_path in playlists:
            self._add_playlist_item(playlist_path)
            
        # Update count
        self.count_label.set_count(len(playlists), "playlists")
        self.count_changed.emit(len(playlists))
        
    def _add_playlist_item(self, playlist_path: Path):
        """Add a playlist item with maintenance styling."""
        try:
            track_count = len(read_m3u(str(playlist_path)))
            
            # Create list item
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, str(playlist_path))
            
            # Create and set specialized maintenance item
            widget = MaintenancePlaylistItem(playlist_path, track_count)
            widget.clicked.connect(lambda p: self.selection_changed.emit(p))
            item.setSizeHint(widget.sizeHint())
            
            # Add to list
            self.playlist_list.addItem(item)
            self.playlist_list.setItemWidget(item, widget)
            self.playlist_items[playlist_path] = widget
            
            # Update analysis state if available
            analysis = self.state.get_analysis(playlist_path)
            if analysis:
                details = []
                if not analysis.exists_remotely:
                    details.append("Not found remotely")
                if analysis.missing_files:
                    details.append(f"{len(analysis.missing_files)} missing files")
                if analysis.has_duplicates:
                    details.append("Has duplicates")
                    
                widget.set_analysis_state(
                    exists_remotely=analysis.exists_remotely,
                    has_errors=len(analysis.missing_files) > 0,
                    has_warnings=analysis.has_duplicates,
                    details=" | ".join(details) if details else None
                )
                
        except Exception as e:
            self.logger.error(f"Error adding playlist {playlist_path}: {e}")
            
    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        if self.current_playlist:
            self.analyze_requested.emit(self.current_playlist)
            
    def _on_repair_clicked(self):
        """Handle repair button click."""
        if self.current_playlist:
            self.repair_requested.emit(self.current_playlist)
            
    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self.current_playlist:
            self.delete_requested.emit(self.current_playlist)
            
    def update_playlist(self, playlist_path: Path, analysis):
        """Update playlist display with analysis results."""
        if playlist_path in self.playlist_items:
            widget = self.playlist_items[playlist_path]
            
            details = []
            if not analysis.exists_remotely:
                details.append("Not found remotely")
            if analysis.missing_files:
                details.append(f"{len(analysis.missing_files)} missing files")
            if analysis.has_duplicates:
                details.append("Has duplicates")
                
            widget.set_analysis_state(
                exists_remotely=analysis.exists_remotely,
                has_errors=len(analysis.missing_files) > 0,
                has_warnings=analysis.has_duplicates,
                details=" | ".join(details) if details else None
            )

    def connect_signals(self):
        """Connect signal handlers."""
        super().connect_signals()
        
        # Connect selection change to button state updates
        def update_button_states(playlist_path):
            enabled = playlist_path is not None
            self.analyze_btn.setEnabled(enabled)
            self.repair_btn.setEnabled(enabled)
            self.delete_btn.setEnabled(enabled)
            
        self.selection_changed.connect(update_button_states)
        
        # Connect to state signals
        if hasattr(self.state, 'analysis_completed'):
            self.state.analysis_completed.connect(self.update_playlist)