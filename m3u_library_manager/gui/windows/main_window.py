from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from pathlib import Path

from .pages.curation_page import CurationPage
from .pages.sync_page import SyncPage
from .pages.explore_page import ExplorePage

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
        self.setup_ui()
        
    def setup_ui(self):
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
        
        # Close button
        close_btn = QLabel("x")
        close_btn.setFixedSize(30, 30)  # Square button
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
        close_btn.mousePressEvent = lambda e: self.close()
        title_layout.addWidget(close_btn)
        
        header_layout.addWidget(title_bar)
        
        # Navigation bar
        nav_bar = QWidget()
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(16, 0, 16, 0)
        nav_layout.setSpacing(24)
        
        # Navigation buttons
        self.nav_buttons = {
            'curation': NavigationButton("Curation"),
            'sync': NavigationButton("Sync"),
            'explore': NavigationButton("Explore")
        }
        
        for btn in self.nav_buttons.values():
            nav_layout.addWidget(btn)
            btn.mousePressEvent = lambda e, b=btn: self.switch_page(b.text().lower())
            
        nav_layout.addStretch()
        header_layout.addWidget(nav_bar)
        
        layout.addWidget(header)
        
        # Content area
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #202020;")
        
        # Initialize pages
        self.pages = {
            'curation': CurationPage(),
            'sync': SyncPage(),
            'explore': ExplorePage()
        }
        
        for name, page in self.pages.items():
            self.content.addWidget(page)
            
        layout.addWidget(self.content)
        
        # Start with curation page
        self.switch_page('curation')
        
    def switch_page(self, page_name: str):
        """Switch to specified page and update navigation"""
        if page_name in self.pages:
            self.content.setCurrentWidget(self.pages[page_name])
            for name, btn in self.nav_buttons.items():
                btn.set_active(name == page_name)
    
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
