# gui/windows/pages/maintenance/components/file_locator_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class FileLocatorPanel(QWidget):
    """Panel for locating missing files."""
    
    def __init__(self, state, on_locate=None):
        super().__init__()
        self.state = state
        self.on_locate = on_locate
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("File Locator Panel"))