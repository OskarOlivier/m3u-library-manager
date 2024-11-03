# gui/windows/pages/explore_page.py

from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

from gui.windows.pages import BasePage

class ExplorePage(BasePage):
    def setup_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Explore Page - Coming Soon")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white;")
        layout.addWidget(label)