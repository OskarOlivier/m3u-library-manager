# gui/components/widgets/playlist_item.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from pathlib import Path

from gui.components.styles.colors import (
    TEXT_COLOR,
    SECONDARY_TEXT,
    BACKGROUND_COLOR,
    ITEM_HOVER,
    ITEM_SELECTED
)
from gui.components.styles.fonts import TEXT_FONT
from gui.components.styles.layouts import (
    WIDGET_MARGINS,
    WIDGET_SPACING,
    PLAYLIST_ITEM_LAYOUT
)

class PlaylistItem(QWidget):
    """Base playlist item widget that only handles display and click events."""
    clicked = pyqtSignal(Path)
    
    def __init__(self, playlist_path: Path, track_count: int, parent=None):
        super().__init__(parent)
        self.playlist_path = playlist_path
        self.track_count = track_count
        self._selected = False
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(PLAYLIST_ITEM_LAYOUT['height'])
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.setup_ui()
        self.update_style()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*WIDGET_MARGINS)
        layout.setSpacing(WIDGET_SPACING)
        
        # Name label
        self.name_label = QLabel(self.playlist_path.stem)
        self.name_label.setFont(TEXT_FONT)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.name_label)
        
        # Count label
        self.status_label = QLabel(str(self.track_count))
        self.status_label.setFont(TEXT_FONT)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.status_label.setMinimumWidth(PLAYLIST_ITEM_LAYOUT['count_width'])
        self.status_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.status_label)
        
    def update_style(self):
        """Update visual appearance based on selection state."""
        base_style = f"""
            {self.__class__.__name__} {{
                background-color: {ITEM_SELECTED if self._selected else BACKGROUND_COLOR};
                border-radius: 4px;
                padding: {PLAYLIST_ITEM_LAYOUT['padding']}px;
            }}
            {self.__class__.__name__}:hover {{
                background-color: {ITEM_HOVER};
            }}
        """
        
        text_color = TEXT_COLOR
        status_color = TEXT_COLOR if self._selected else SECONDARY_TEXT
        
        self.setStyleSheet(base_style)
        self.name_label.setStyleSheet(f"color: {text_color}; background: transparent;")
        self.status_label.setStyleSheet(f"color: {status_color}; background: transparent;")
        
    def set_selected(self, selected: bool):
        """Update selection state - called by panel."""
        if self._selected != selected:
            self._selected = selected
            self.update_style()
            
    def update_count(self, count: int):
        self.track_count = count
        self.status_label.setText(str(count))
        
    def update_status(self, status: str):
        self.status_label.setText(status)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Just emit clicked signal - panel handles selection
            self.clicked.emit(self.playlist_path)