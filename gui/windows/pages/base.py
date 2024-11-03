"""Base page implementation."""
from PyQt6.QtWidgets import QWidget

class BasePage(QWidget):
    """Base class for all pages."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components."""
        pass
