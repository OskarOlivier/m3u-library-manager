from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

class BasePage(QWidget):
    """Base class for all pages"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Override in subclasses"""
        pass
