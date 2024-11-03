# gui/windows/playlist_manager.py

from PyQt6.QtWidgets import QLabel, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path

class PlaylistItem(QWidget):
    """Interactive playlist item with separated title and count aligned to edges."""

    def __init__(self, playlist_path: Path, track_count: int, click_handler=None, parent=None):
        super().__init__(parent)
        self.playlist_path = playlist_path
        self.track_count = track_count
        self.highlighted = False
        self.click_handler = click_handler

        # Ensure PlaylistItem stretches to fill available horizontal space
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.init_ui()

    def init_ui(self):
        # Main layout for the item, with padding to keep labels aligned to edges
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 6, 10, 6)
        main_layout.setSpacing(0)

        # Title label aligned to the left
        self.title_label = QLabel(self.playlist_path.stem, self)
        self.title_label.setFont(QFont("Segoe UI", 10))
        self.title_label.setStyleSheet("color: white; padding-left: 5px;")  # Padding for title
        main_layout.addWidget(self.title_label)

        # Spacer to push the count label to the far right
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        main_layout.addItem(spacer)

        # Count label aligned to the right
        self.count_label = QLabel(str(self.track_count), self)
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: lightgrey; padding-right: 5px;")  # Padding for count
        main_layout.addWidget(self.count_label)

        # Apply the initial style
        self.update_style()

    def update_display(self, new_count: int = None):
        """
        Update the playlist display with a new count (if provided)
        and refresh the style.
        """
        if new_count is not None:
            self.track_count = new_count
            self.count_label.setText(str(self.track_count))
        self.update_style()

    def update_style(self):
        # Style management on the parent container for highlighting
        style = f"""
            QWidget {{
                background-color: {"#0078D4" if self.highlighted else "#2D2D2D"};
                border-radius: 4px;
            }}
        """
        self.setStyleSheet(style)

    def mousePressEvent(self, event):
        """Handle click event and emit the playlist path if click_handler is defined."""
        if event.button() == Qt.MouseButton.LeftButton and self.click_handler:
            self.click_handler.clicked.emit(self.playlist_path)

