# gui/windows/pages/maintenance/components/sort_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SortPanel(QWidget):
    """Panel for sorting playlist files."""
    
    def __init__(self, state, on_sort=None):
        super().__init__()
        self.state = state
        self.on_sort = on_sort
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sort Panel"))