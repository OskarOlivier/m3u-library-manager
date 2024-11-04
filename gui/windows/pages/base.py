# gui/windows/pages/base.py
"""Base page implementation."""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

class BasePage(QWidget):
    """Base class for all pages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components."""
        pass