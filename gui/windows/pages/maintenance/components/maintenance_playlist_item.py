# gui/windows/pages/maintenance/components/maintenance_playlist_item.py
from PyQt6.QtCore import Qt
from typing import Optional
from gui.components.widgets.playlist_item import PlaylistItem
from gui.components.styles.colors import (
    TEXT_COLOR,
    SUCCESS_COLOR,
    ERROR_COLOR,
    WARNING_COLOR
)
from pathlib import Path

class MaintenancePlaylistItem(PlaylistItem):
    """Playlist item with matching sync panel selection behavior."""
    def __init__(self, playlist_path: Path, track_count: int, parent=None):
        self._has_errors = False
        self._has_warnings = False
        self._exists_remotely = True
        self._details: Optional[str] = None
        super().__init__(playlist_path, track_count, parent)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(not self._selected)
            self.clicked.emit(self.playlist_path)

    def update_style(self):
        # Determine text color based on selection state first
        if self._selected:
            text_color = TEXT_COLOR  # Always white when selected
        else:
            # Use status colors when not selected
            if self._has_errors:
                text_color = ERROR_COLOR
            elif self._has_warnings:
                text_color = WARNING_COLOR
            else:
                text_color = SUCCESS_COLOR  # Green for no issues
            
        super().update_style()  # This handles selection background
        
        # Override text colors
        self.name_label.setStyleSheet(f"color: {text_color}; background: transparent;")
        self.status_label.setStyleSheet(f"color: {text_color}; background: transparent; opacity: 0.8;")
        
        if self._details:
            self.setToolTip(self._details)

    def set_analysis_state(self, exists_remotely: bool, has_errors: bool, 
                         has_warnings: bool, details: Optional[str] = None):
        """Set analysis state and update visuals."""
        self._exists_remotely = exists_remotely
        self._has_errors = has_errors
        self._has_warnings = has_warnings
        self._details = details
        self.update_style()