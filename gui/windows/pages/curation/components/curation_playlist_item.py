# gui/windows/pages/curation/components/curation_playlist_item.py

from PyQt6.QtCore import Qt
import subprocess
import logging

from gui.components.widgets.playlist_item import PlaylistItem
from gui.components.styles.colors import (
    TEXT_COLOR,
    SUCCESS_COLOR,
    ERROR_COLOR,
    WARNING_COLOR,
    ITEM_HOVER,
    ITEM_SELECTED,
    BACKGROUND_COLOR
)
from pathlib import Path

class CurationPlaylistItem(PlaylistItem):
    """Playlist item with visual selection state and error/warning indicators."""

    def __init__(self, playlist_path: Path, track_count: int, parent=None):
        self._has_errors = False
        self._has_warnings = False
        self._exists_remotely = True
        self._details: Optional[str] = None
        self.logger = logging.getLogger(f'curation_playlist_item_{playlist_path.stem}')
        self.logger.setLevel(logging.INFO)
        super().__init__(playlist_path, track_count, parent)
        
    def mousePressEvent(self, event):
        """Handle mouse click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.logger.debug(f"Left click on {self.playlist_path.name} (currently selected: {self._selected})")
            # Let the click propagate to signal handlers
            self.clicked.emit(self.playlist_path)
        elif event.button() == Qt.MouseButton.RightButton:
            # Open playlist in dopamine.exe
            try:
                self.logger.debug(f"Opening {self.playlist_path.name} in Dopamine")
                subprocess.run(['C:\\Program Files (x86)\\Dopamine\\dopamine.exe', self.playlist_path], check=True)
            except FileNotFoundError:
                self.logger.error("dopamine.exe not found. Please ensure it is installed and in your PATH.")
            except Exception as e:
                self.logger.error(f"Failed to open playlist: {e}")

    def set_selected(self, selected: bool):
        """Update selection state with visual feedback."""
        if self._selected != selected:
            self.logger.debug(f"Selection state changing from {self._selected} to {selected}")
            self._selected = selected
            self.update_style()
            self.setProperty("selected", selected)  # For style sheets
            self.style().unpolish(self)  # Force style update
            self.style().polish(self)
            self.update()

    def update_style(self):
        """Update visual appearance based on selection and other states."""
        # Determine background color
        if self._selected:
            bg_color = ITEM_SELECTED
        else:
            bg_color = BACKGROUND_COLOR

        # Determine text color - prioritize selection state
        if self._selected:
            text_color = TEXT_COLOR  # Always white when selected
        else:
            # Use status colors when not selected
            if not self._exists_remotely:
                text_color = ERROR_COLOR
            elif self._has_errors:
                text_color = ERROR_COLOR
            elif self._has_warnings:
                text_color = WARNING_COLOR
            else:
                text_color = TEXT_COLOR
            
        # Apply styles with specific states
        self.setStyleSheet(f"""
            CurationPlaylistItem {{
                background-color: {bg_color};
                border-radius: 4px;
                padding: 8px;
            }}
            CurationPlaylistItem:hover {{
                background-color: {ITEM_HOVER if not self._selected else ITEM_SELECTED};
            }}
            CurationPlaylistItem[selected="true"] {{
                background-color: {ITEM_SELECTED};
            }}
        """)
        
        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background: transparent;
            }}
        """)
        
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background: transparent;
                opacity: 0.8;
            }}
        """)
        
        if self._details:
            self.setToolTip(self._details)

    def update_count(self, count: int):
        """Update the track count display."""
        self.logger.debug(f"Updating count to {count}")
        self.track_count = count
        self.status_label.setText(str(count))
        
    def set_error_state(self, has_error: bool):
        """Set error state with visual feedback."""
        if self._has_errors != has_error:
            self.logger.debug(f"Error state changing from {self._has_errors} to {has_error}")
            self._has_errors = has_error
            self.update_style()
            
    def set_warning_state(self, has_warning: bool):
        """Set warning state with visual feedback."""
        if self._has_warnings != has_warning:
            self.logger.debug(f"Warning state changing from {self._has_warnings} to {has_warning}")
            self._has_warnings = has_warning
            self.update_style()
            
    def set_remote_existence(self, exists: bool):
        """Set remote existence state with visual feedback."""
        if self._exists_remotely != exists:
            self.logger.debug(f"Remote existence changing from {self._exists_remotely} to {exists}")
            self._exists_remotely = exists
            self.update_style()
            
    def set_details(self, details: str):
        """Set detail text for tooltip."""
        self._details = details
        self.update_style()

    def enterEvent(self, event):
        """Handle mouse enter event."""
        self.logger.debug(f"Mouse entered {self.playlist_path.name}")
        super().enterEvent(event)
        self.update_style()

    def leaveEvent(self, event):
        """Handle mouse leave event."""
        self.logger.debug(f"Mouse left {self.playlist_path.name}")
        super().leaveEvent(event)
        self.update_style()