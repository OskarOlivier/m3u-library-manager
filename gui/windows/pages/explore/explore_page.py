# gui/windows/pages/explore/explore_page.py

from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

from ..base import BasePage

class ExplorePage(BasePage):
    def setup_ui(self):
        """Set up the explore page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Music Library Explorer")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)
        
        # Coming soon message
        message = QLabel("Coming Soon: Advanced music library exploration features")
        message.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 16px;
            }
        """)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        layout.addStretch()

    def cleanup(self):
        """Clean up resources when page is closed."""
        pass