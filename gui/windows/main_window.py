# gui/windows/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QStackedWidget, QApplication)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QFont
from pathlib import Path
import logging

from .pages.base import BasePage
from .pages.curation_page import CurationPage
from .pages.sync.sync_page import SyncPage
from .pages.explore.explore_page import ExplorePage
from .pages.maintenance.maintenance_page import MaintenancePage

class NavigationButton(QLabel):
    """Custom navigation button with highlight states"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.active = False
        self.setup_ui()
        
    def setup_ui(self):
        self.setFont(QFont("Segoe UI", 11))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContentsMargins(16, 8, 16, 8)
        self.update_style()
        
    def update_style(self):
        if self.active:
            style = """
                QLabel {
                    color: white;
                    border-bottom: 2px solid #0078D4;
                    padding-bottom: 6px;
                }
            """
        else:
            style = """
                QLabel {
                    color: #999999;
                    padding-bottom: 8px;
                }
                QLabel:hover {
                    color: white;
                }
            """
        self.setStyleSheet(style)
        
    def set_active(self, active: bool):
        self.active = active
        self.update_style()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(flags=Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.oldPos = None
        self.pages = {}
        self.nav_buttons = {}
        self.current_page = None
        self.is_quitting = False
        self.logger = logging.getLogger('MainWindow')
        
        # Initialize pages first
        self.init_pages()
        self.setup_ui()
        self.center_on_screen()
        
    def init_pages(self):
        """Initialize all pages before UI setup"""
        try:
            self.pages = {
                'curation': CurationPage(),
                'sync': SyncPage(),
                'maintenance': MaintenancePage(),
                'explore': ExplorePage()
            }
            self.logger.debug(f"Initialized pages: {list(self.pages.keys())}")
        except Exception as e:
            self.logger.error(f"Error initializing pages: {e}", exc_info=True)
            raise
        
    def setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle("M3U Library Manager")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title, navigation, and close button
        header = QWidget()
        header.setStyleSheet("background-color: #1E1E1E;")
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar with close button
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 8, 8, 8)
        
        # Window title
        title = QLabel("M3U Library Manager")
        title.setFont(QFont("Segoe UI", 10))
        title.setStyleSheet("color: #999999;")
        title_layout.addWidget(title)
        
        close_btn = QLabel("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setFont(QFont("Segoe UI", 14))
        close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_btn.setStyleSheet("""
            QLabel {
                color: #999999;
                background: transparent;
            }
            QLabel:hover {
                color: white;
                background-color: #E81123;
            }
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.mousePressEvent = lambda e: self.hide()  # Just hide instead of quitting
        title_layout.addWidget(close_btn)
        
        header_layout.addWidget(title_bar)
        
        # Navigation bar
        nav_bar = QWidget()
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(16, 0, 16, 0)
        nav_layout.setSpacing(24)
        
        # Navigation buttons
        nav_pages = [
            ('curation', "Curation"),
            ('sync', "Sync"),
            ('maintenance', "Maintenance"),
            ('explore', "Explore")
        ]
        
        self.nav_buttons = {}
        for page_id, label in nav_pages:
            btn = NavigationButton(label)
            self.nav_buttons[page_id] = btn
            nav_layout.addWidget(btn)
            # Using partial to capture the page_id correctly
            from functools import partial
            btn.mousePressEvent = partial(self._on_nav_click, page_id)
            
        nav_layout.addStretch()
        header_layout.addWidget(nav_bar)
        
        layout.addWidget(header)
        
        # Content area
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #202020;")
        
        # Add pages to content
        for name, page in self.pages.items():
            self.content.addWidget(page)
            
        layout.addWidget(self.content)
        
        # Start with curation page
        self.switch_page('curation')
        
    def _on_nav_click(self, page_id, event):
        """Handle navigation button clicks."""
        self.switch_page(page_id)

    def switch_page(self, page_name: str):
        """Switch to specified page and update navigation"""
        if page_name not in self.pages or self.is_quitting:
            return
            
        try:
            # Clean up previous page if needed
            if self.current_page and hasattr(self.pages[self.current_page], 'cleanup'):
                self.pages[self.current_page].cleanup()
                
            self.content.setCurrentWidget(self.pages[page_name])
            self.current_page = page_name
            
            # Update navigation buttons
            for name, btn in self.nav_buttons.items():
                btn.set_active(name == page_name)
                
        except Exception as e:
            self.logger.error(f"Error switching to page {page_name}: {e}")
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None:
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.oldPos = None
        
    def center_on_screen(self):
        """Center window on primary screen"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        center_point = screen_geometry.center()
        
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def hideEvent(self, event):
        """Handle window hide events."""
        super().hideEvent(event)
        self.logger.debug("Window hidden")

    def closeEvent(self, event):
        """Handle window close events - always minimize to tray."""
        self.logger.debug("Minimizing to system tray")
        event.ignore()
        self.hide()

    def cleanup_application(self):
        """Clean up resources when application is actually quitting."""
        try:
            # Clean up current page
            if self.current_page and self.pages.get(self.current_page):
                page = self.pages[self.current_page]
                if hasattr(page, 'cleanup'):
                    self.logger.debug(f"Cleaning up current page: {self.current_page}")
                    page.cleanup()

            # Clean up other pages
            for name, page in self.pages.items():
                if name != self.current_page and hasattr(page, 'cleanup'):
                    self.logger.debug(f"Cleaning up page: {name}")
                    page.cleanup()

            # Clear references
            self.pages.clear()
            self.nav_buttons.clear()
            self.current_page = None

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)
