# gui/widgets/playlist_widgets.py

from PyQt6.QtWidgets import QLabel, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from pathlib import Path

__all__ = ['PlaylistItem', 'ClickHandler']

class ClickHandler(QObject):
    """Signal handler for playlist clicks"""
    clicked = pyqtSignal(Path)

class PlaylistItem(QWidget):
    """Interactive playlist item with separated title and count aligned to edges."""

    def __init__(self, playlist_path: Path, track_count: int, click_handler: ClickHandler = None, parent=None):
        super().__init__(parent)
        self.playlist_path = playlist_path
        self.track_count = track_count
        self.highlighted = False
        self.click_handler = click_handler

        # Ensure PlaylistItem stretches to fill available horizontal space
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.init_ui()

    def init_ui(self):
        # Create outer layout
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(0)

        # Create container widget for the entire item
        container = QWidget(self)
        outer_layout.addWidget(container)

        # Create layout for content inside container
        content_layout = QHBoxLayout(container)
        content_layout.setContentsMargins(10, 6, 10, 6)
        content_layout.setSpacing(0)

        # Title label aligned to the left
        self.title_label = QLabel(self.playlist_path.stem, container)
        self.title_label.setFont(QFont("Segoe UI", 10))
        self.title_label.setStyleSheet("color: white;")
        content_layout.addWidget(self.title_label)

        # Spacer to push count to the right
        content_layout.addStretch()

        # Count label aligned to the right
        self.count_label = QLabel(str(self.track_count), container)
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: lightgrey;")
        content_layout.addWidget(self.count_label)

        # Set cursor to pointing hand
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Apply the initial style
        self.update_style()

    def update_display(self, new_count: int = None):
        """Update the playlist display with a new count and refresh style."""
        if new_count is not None:
            self.track_count = new_count
            self.count_label.setText(str(self.track_count))
        self.update_style()

    def update_style(self):
        """Update the visual style based on highlight state."""
        # Style for the container widget (first child)
        container_style = f"""
            QWidget {{
                background-color: {"#0078D4" if self.highlighted else "#2D2D2D"};
                border-radius: 4px;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """
        self.findChild(QWidget).setStyleSheet(container_style)

    def mousePressEvent(self, event):
        """Handle click event and emit the playlist path."""
        if event.button() == Qt.MouseButton.LeftButton and self.click_handler:
            self.click_handler.clicked.emit(self.playlist_path)