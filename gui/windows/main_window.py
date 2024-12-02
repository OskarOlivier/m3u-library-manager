# gui/windows/main_window.py

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QStackedWidget, QApplication, QPushButton)
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize, QRect, pyqtSignal
from PyQt6.QtGui import QFont, QScreen
from pathlib import Path
import logging

from core.events.event_bus import EventBus
from core.cache.relationship_cache import RelationshipCache
from core.context import ApplicationContext
from .pages.base_page import BasePage
from .pages.curation.curation_page import CurationPage
from .pages.sync.sync_page import SyncPage
from .pages.maintenance.maintenance_page import MaintenancePage
from .pages.explore.explore_page import ExplorePage
from .pages.proximity.proximity_page import ProximityPage
from utils.cache.cleanup import get_unplaylisted_size
from app.config import Config

# Title bar height constants
TITLE_BAR_HEIGHT = 46
NAV_BAR_HEIGHT = 40
HEADER_HEIGHT = TITLE_BAR_HEIGHT + NAV_BAR_HEIGHT

class NavigationButton(QLabel):
    """Custom navigation button with highlight states"""
    
    clicked = pyqtSignal()  # Add signal for click events
    
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
        if self.active != active:
            self.active = active
            self.update_style()
        
    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
        self.setStyleSheet(self.styleSheet() + f"""
            QLabel {{
                color: {'#999999' if enabled else '#666666'};
            }}
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.clicked.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(flags=Qt.WindowType.FramelessWindowHint)

        # Initialize logger
        self.logger = logging.getLogger('MainWindow')
        self.logger.info("Initializing main window")

        # Initialize context and ensure it's ready
        self.context = ApplicationContext.get_instance()
        #if not self.context.is_initialized():
        #    self.logger.info("Initializing application context")
        #    self.context.ensure_initialized(Path(Config.PLAYLISTS_DIR))

        # Initialize tracking variables
        self.oldPos = None
        self.pages = {}
        self.nav_buttons = {}
        self.current_page = None
        self.is_quitting = False

        # Initialize pages and UI
        self.init_pages()
        self.setup_ui()
        
        # Set up fullscreen
        self.make_fullscreen()
        
        # Setup cleanup button update timer
        self.cleanup_update_timer = QTimer(self)
        self.cleanup_update_timer.timeout.connect(self.update_cleanup_button)
        self.cleanup_update_timer.start(5000)  # Update every 5 seconds
        self.update_cleanup_button()

        # Start with curation page
        self.switch_page('curation')
        self.logger.info("Main window initialization complete")

    def make_fullscreen(self):
        """Set up fullscreen mode within screen constraints."""
        try:
            screen = QApplication.primaryScreen()
            if not screen:
                self.logger.error("No screen detected")
                return

            # Get available geometry (excludes taskbar)
            available_geometry = screen.availableGeometry()
            self.logger.debug(f"Screen available geometry: {available_geometry}")

            # Set window geometry to match available screen space
            self.setGeometry(available_geometry)
            
            # Set minimum size to prevent window from being too small
            min_width = min(1024, available_geometry.width())
            min_height = min(768, available_geometry.height())
            self.setMinimumSize(min_width, min_height)
            
            # Show maximized
            self.showMaximized()
            
        except Exception as e:
            self.logger.error(f"Error setting up fullscreen: {e}", exc_info=True)
                   
    def setup_ui(self):
        """Set up the main UI with fullscreen layout."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header (title bar + navigation)
        header = QWidget()
        header.setFixedHeight(HEADER_HEIGHT)
        header.setStyleSheet("background-color: #1E1E1E;")
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar setup
        title_bar = QWidget()
        title_bar.setFixedHeight(TITLE_BAR_HEIGHT)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 8, 8, 8)
        
        # Window title
        title = QLabel("M3U Library Manager")
        title.setFont(QFont("Segoe UI", 10))
        title.setStyleSheet("color: #999999;")
        title_layout.addWidget(title)
        
        # Cleanup button
        self.cleanup_button = QPushButton("Clean 0KB cache")
        self.cleanup_button.setFont(QFont("Segoe UI", 10))
        self.cleanup_button.setStyleSheet("""
            QPushButton {
                color: #999999;
                background: transparent;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: white;
            }
            QPushButton:pressed {
                color: #666666;
            }
            QPushButton:disabled {
                color: #666666;
            }
        """)
        self.cleanup_button.clicked.connect(self.cleanup_cache)
        title_layout.addWidget(self.cleanup_button)
        
        # Close button
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
        close_btn.mousePressEvent = lambda e: self.hide()
        title_layout.addWidget(close_btn)
        
        # Navigation bar setup
        nav_bar = QWidget()
        nav_bar.setFixedHeight(NAV_BAR_HEIGHT)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(16, 0, 16, 0)
        nav_layout.setSpacing(24)
        
        # Navigation buttons
        nav_pages = [
            ('curation', "Curation"),
            ('sync', "Sync"),
            ('maintenance', "Maintenance"),
            ('explore', "Explore"),
            ('proximity', "Proximity")
        ]
        
        self.nav_buttons = {}
        for page_id, label in nav_pages:
            btn = NavigationButton(label)
            self.nav_buttons[page_id] = btn
            btn.clicked.connect(lambda pid=page_id: self.switch_page(pid))
            nav_layout.addWidget(btn)
            
        nav_layout.addStretch()
        
        # Add title bar and nav bar to header
        header_layout.addWidget(title_bar)
        header_layout.addWidget(nav_bar)
        layout.addWidget(header)
        
        # Content area
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #202020;")
        
        # Add pages to content
        for name, page in self.pages.items():
            self.content.addWidget(page)
            
        layout.addWidget(self.content)
       
    def init_pages(self):
        """Initialize all pages."""
        try:
            self.logger.debug("Initializing pages")
            self.pages = {
                'curation': CurationPage(),
                'sync': SyncPage(),
                'maintenance': MaintenancePage(),
                'explore': ExplorePage(),
                'proximity': ProximityPage()
            }
            
            # Pass context to pages that need it
            for page in self.pages.values():
                if hasattr(page, 'set_context'):
                    page.set_context(self.context)
                    
            self.logger.debug(f"Initialized pages: {list(self.pages.keys())}")
        except Exception as e:
            self.logger.error(f"Error initializing pages: {e}")
            raise
            
    def update_cleanup_button(self):
        """Update the cleanup button text with current cache size"""
        try:
            size_kb, count = get_unplaylisted_size(Path(Config.PLAYLISTS_DIR))
            self.cleanup_button.setText(f"Clean {size_kb:,}KB cache")
            self.cleanup_button.setEnabled(size_kb > 0)
        except Exception as e:
            self.logger.error(f"Error updating cleanup button: {e}")
            self.cleanup_button.setText("Clean cache")
            self.cleanup_button.setEnabled(False)

    def cleanup_cache(self):
        """Handle cleanup button click"""
        try:
            from utils.cache.cleanup import cleanup_unplaylisted
            size_cleaned, files_removed = cleanup_unplaylisted(Path(Config.PLAYLISTS_DIR))
            self.logger.info(f"Cleaned {size_cleaned:,}KB from {files_removed} files")
            self.update_cleanup_button()
        except Exception as e:
            self.logger.error(f"Error cleaning cache: {e}")

    def switch_page(self, page_name: str):
        """Switch to specified page and update navigation."""
        if page_name not in self.pages or self.is_quitting:
            return
            
        try:
            self.content.setCurrentWidget(self.pages[page_name])
            self.current_page = page_name
            
            # Update navigation buttons
            for name, btn in self.nav_buttons.items():
                btn.set_active(name == page_name)
                
        except Exception as e:
            self.logger.error(f"Error switching to page {page_name}: {e}")
            
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        # Disable dragging in fullscreen
        pass

    def mouseReleaseEvent(self, event):
        """Handle end of window dragging."""
        self.oldPos = None

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
            self.logger.debug("Starting application cleanup")
            self.is_quitting = True
            
            # Stop cleanup timer
            if hasattr(self, 'cleanup_update_timer'):
                self.cleanup_update_timer.stop()

            # Clean up pages
            for name, page in self.pages.items():
                if hasattr(page, 'cleanup'):
                    self.logger.debug(f"Cleaning up page: {name}")
                    page.cleanup()

            # Clear references
            self.pages.clear()
            self.nav_buttons.clear()
            self.current_page = None

            # Clean up context last
            self.context.cleanup()

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)