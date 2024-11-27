# gui/windows/pages/explore/explore_page.py

from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
import logging
import traceback

from ..base_page import BasePage

class ExplorePage(BasePage):
    def __init__(self, parent=None):
        self.logger = logging.getLogger('explore_page')
        super().__init__(parent)

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
        try:
            self.logger.debug("Starting explore page cleanup")
            # Add any specific cleanup here when needed
            BasePage.cleanup(self)
            self.logger.debug("Explore page cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during explore page cleanup: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            self.logger.debug("Explore page cleanup finished")