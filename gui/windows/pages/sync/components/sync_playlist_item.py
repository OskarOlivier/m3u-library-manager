# gui/windows/pages/sync/components/sync_playlist_item.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from gui.components.widgets.playlist_item import PlaylistItem
from gui.components.styles.colors import (
   TEXT_COLOR,
   SUCCESS_COLOR,
   ERROR_COLOR,
   WARNING_COLOR
)
from pathlib import Path


class SyncPlaylistItem(PlaylistItem):
    def __init__(self, playlist_path: Path, track_count: int, parent=None):
       self._exists_remotely = True
       self._missing_remotely = 0
       self._missing_locally = 0
       self._is_synced = False  # New flag to track sync status
       super().__init__(playlist_path, track_count, parent)
       
    def update_style(self):
       # Determine text color based on selection state first
       if self._selected:
           text_color = TEXT_COLOR  # Always white when selected
       else:
           # Use status colors when not selected
           if not self._exists_remotely:
               text_color = ERROR_COLOR
           elif self._missing_remotely > 0 or self._missing_locally > 0:
               text_color = WARNING_COLOR
           elif self._is_synced:
               text_color = SUCCESS_COLOR  # Green for successfully synced
           else:
               text_color = TEXT_COLOR
           
       super().update_style()  # This handles selection background
       
       # Override text colors
       self.name_label.setStyleSheet(f"color: {text_color}; background: transparent;")
       self.status_label.setStyleSheet(f"color: {text_color}; background: transparent; opacity: 0.8;")
       
       tooltip = "Playlist not found on remote" if not self._exists_remotely else (
           " | ".join([
               f"{self._missing_remotely} missing remotely" if self._missing_remotely > 0 else "",
               f"{self._missing_locally} missing locally" if self._missing_locally > 0 else ""
           ]).strip() or "Fully synced"
       )
       self.setToolTip(tooltip)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Find parent list widget
            parent_list = self.parent()
            while parent_list and not isinstance(parent_list, QListWidget):
                parent_list = parent_list.parent()
                
            if parent_list:
                # Let Qt handle the selection through standard mechanism
                for i in range(parent_list.count()):
                    item = parent_list.item(i)
                    if parent_list.itemWidget(item) == self:
                        parent_list.setCurrentItem(item)
                        break

        super().mousePressEvent(event)

    def set_sync_state(self, exists_remotely: bool, missing_remotely: int, missing_locally: int):
       self._exists_remotely = exists_remotely
       self._missing_remotely = missing_remotely
       self._missing_locally = missing_locally
       
       # Update sync status
       self._is_synced = exists_remotely and missing_remotely == 0 and missing_locally == 0
       
       if not exists_remotely:
           self.update_status("Not found")
       elif missing_remotely > 0 or missing_locally > 0:
           total_diffs = missing_remotely + missing_locally
           self.update_status(f"Unsynced: {total_diffs}")
       else:
           self.update_status("Synced")
           
       self.update_style()
        
    @property
    def has_differences(self) -> bool:
        return self._missing_remotely > 0 or self._missing_locally > 0
        
    @property
    def exists_remotely(self) -> bool:
        return self._exists_remotely
        
    @property
    def is_synced(self) -> bool:
        return self._is_synced