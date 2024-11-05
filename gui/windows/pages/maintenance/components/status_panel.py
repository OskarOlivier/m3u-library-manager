# gui/windows/pages/maintenance/components/status_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class StatusPanel(QWidget):
    """Panel for showing status and progress."""
    
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Status Panel"))