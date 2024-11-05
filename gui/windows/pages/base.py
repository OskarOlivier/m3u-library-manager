# gui/windows/pages/base.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

class BasePage(QWidget):
    """Base class for all pages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #202020;")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components. Must be implemented by subclasses."""
        raise NotImplementedError
        
    def cleanup(self):
        """Clean up resources. Should be implemented by subclasses if needed."""
        pass