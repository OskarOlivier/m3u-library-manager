# gui/dialogs/base_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QApplication, QWidget)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont

class BaseDialog(QDialog):
    """Base dialog class with consistent styling for all application dialogs."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(title)
        self.setFixedWidth(400)
        self.setup_base_ui()
        
    def setup_base_ui(self):
        """Set up the base UI components and styling."""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(24, 24, 24, 24)
        
        # Title label
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setFont(QFont("Segoe UI", 11))
        self.layout.addWidget(self.title_label)
        
        # Content container
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(16)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.content)
        
        # Button container
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(12)
        
        # Default buttons (can be overridden)
        self.cancel_btn = self._create_button("Cancel", 
                                            self.reject,
                                            is_default=False)
        self.ok_btn = self._create_button("OK", 
                                         self.accept,
                                         is_default=True)
        
        self.button_layout.addWidget(self.cancel_btn)
        self.button_layout.addWidget(self.ok_btn)
        
        self.layout.addLayout(self.button_layout)
        
        # Apply dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: #202020;
                border: 1px solid #404040;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
            QLineEdit {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
                padding: 8px;
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
            QLineEdit:focus {
                background-color: #333333;
            }
        """)
        
    def _create_button(self, text: str, callback=None, is_default: bool = False) -> QPushButton:
        """Create a styled button."""
        button = QPushButton(text)
        button.setFont(QFont("Segoe UI", 11))
        if callback:
            button.clicked.connect(callback)
            
        # Style based on default state
        base_color = "#0078D4" if is_default else "#2D2D2D"
        hover_color = "#1982D4" if is_default else "#404040"
        pressed_color = "#106EBE" if is_default else "#505050"
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)
        
        button.setDefault(is_default)
        return button
        
    def showEvent(self, event):
        """Center dialog on parent or screen when shown."""
        super().showEvent(event)
        # Force processing of all pending events to ensure window is rendered
        QApplication.processEvents()
        self.center_on_parent_or_screen()
        
    def center_on_parent_or_screen(self):
        """Center the dialog on parent window or screen."""
        if self.parent() and self.parent().isVisible():
            # Center on parent
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2
            )
        else:
            # Center on screen
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                center_point = screen_geometry.center()
                
                frame_geometry = self.frameGeometry()
                frame_geometry.moveCenter(center_point)
                self.move(frame_geometry.topLeft())