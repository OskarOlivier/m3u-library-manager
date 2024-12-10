# gui/windows/pages/base_page.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

class BasePage(QWidget):
    """Base class for all pages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #202020;")
    
    def init_page(self):
        """Initialize page components. Must be implemented by subclasses."""
        pass
        
    def setup_ui(self):
        """Setup the UI components. Must be implemented by subclasses."""
        pass
        
    def cleanup(self):
        """Base cleanup method. Can be extended by subclasses."""
        try:
            self.logger.debug(f"Starting base cleanup for {self.__class__.__name__}")
        except Exception as e:
            self.logger.error(f"Error in base cleanup: {str(e)}\n{traceback.format_exc()}")