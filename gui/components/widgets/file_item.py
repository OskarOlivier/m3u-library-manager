# gui/components/widgets/file_item.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
import logging

from gui.components.styles.colors import (
    TEXT_COLOR,
    BACKGROUND_COLOR,
    ITEM_HOVER,
    ITEM_SELECTED,
    SECONDARY_TEXT,
)
from gui.components.styles.fonts import TEXT_FONT
from gui.components.styles.layouts import (
    WIDGET_MARGINS,
    WIDGET_SPACING,
    PLAYLIST_ITEM_LAYOUT
)

class FileItem(QWidget):
    """Widget representing a single file with checkbox and label."""
    
    checkbox_changed = pyqtSignal(bool)  # Emits when checkbox state changes
    
    def __init__(self, file_path: Path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Layout setup
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*WIDGET_MARGINS)
        layout.setSpacing(WIDGET_SPACING)
        
        # Fixed height to match playlist items
        self.setFixedHeight(PLAYLIST_ITEM_LAYOUT['height'])
        
        # Checkbox with custom styling
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(20, 20)
        self.checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #404040;  /* Light grey background */
                border: none;
                border-radius: 3px;
            }
            QCheckBox::indicator:hover {
                background-color: #505050;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D4;
            }
        """)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)
        
        # Filename label
        self.label = QLabel(self.file_path.name)
        self.label.setFont(TEXT_FONT)
        self.label.setStyleSheet(f"color: {TEXT_COLOR};")
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, 
                               QSizePolicy.Policy.Preferred)
        layout.addWidget(self.label)
        
        # Set widget styling
        self.setStyleSheet(f"""
            FileItem {{
                background-color: {BACKGROUND_COLOR};
                border-radius: 4px;
                padding: {PLAYLIST_ITEM_LAYOUT['padding']}px;
            }}
            FileItem:hover {{
                background-color: {ITEM_HOVER};
            }}
        """)
            
    def _on_checkbox_changed(self, state: int):
        """Handle checkbox state changes."""
        self.checkbox_changed.emit(bool(state))
        
    def is_checked(self) -> bool:
        """Get checkbox state."""
        return self.checkbox.isChecked()
        
    def set_checked(self, checked: bool, emit: bool = True):
        """
        Set checkbox state.
        
        Args:
            checked: New checkbox state
            emit: Whether to emit state change signal
        """
        if emit:
            old_state = self.checkbox.isChecked()
            self.checkbox.setChecked(checked)
            if old_state != checked:
                self.checkbox_changed.emit(checked)
        else:
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(checked)
            self.checkbox.blockSignals(False)
        
    def set_error_state(self, is_error: bool):
        """Set error styling for the item."""
        color = "#FF4444" if is_error else TEXT_COLOR
        self.label.setStyleSheet(f"color: {color}; background: transparent;")