# gui/windows/main_window.py

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QStackedWidget, QApplication, QPushButton)
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize, QRect
from PyQt6.QtGui import QFont, QScreen
from pathlib import Path
import logging

from core.events.event_bus import EventBus  
from core.cache.relationship_cache import RelationshipCache
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
        super().__init__(flags=Qt.WindowType.FramelessWindowHint)

        # Initialize logger
        self.logger = logging.getLogger('MainWindow')

        # Get core system instances
        self.event_bus = EventBus.get_instance()
        self.cache = RelationshipCache.get_instance()
        
        # Initialize tracking variables
        self.oldPos = None
        self.pages = {}
        self.nav_buttons = {}
        self.current_page = None
        self.is_quitting = False

        # Initialize pages first
        self.init_pages()
        self.setup_ui()
        
        # Set up fullscreen
        self.make_fullscreen()
        
        # Setup cleanup button update timer
        self.cleanup_update_timer = QTimer(self)
        self.cleanup_update_timer.timeout.connect(self.update_cleanup_button)
        self.cleanup_update_timer.start(5000)  # Update every 5 seconds
        self.update_cleanup_button()

        # Connect cache events
        self.cache.initialized.connect(self._on_cache_initialized)
        self.cache.error_occurred.connect(self._on_cache_error)
        self.event_bus.event_occurred.connect(self._handle_event)
        
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
            nav_layout.addWidget(btn)
            from functools import partial
            btn.mousePressEvent = partial(self._on_nav_click, page_id)
            
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
        
        # Start with curation page
        self.switch_page('curation')
       
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
            self.logger.debug(f"Initialized pages: {list(self.pages.keys())}")
        except Exception as e:
            self.logger.error(f"Error initializing pages: {e}")
            raise

    def _on_cache_initialized(self):
        """Handle cache initialization completion."""
        self.logger.info("Cache initialization complete")
        # Notify pages that need cache data
        if 'curation' in self.pages:
            self.pages['curation'].refresh_playlists()
        if 'proximity' in self.pages:
            self.pages['proximity'].update_visualization()

    def _on_cache_error(self, error: str):
        """Handle cache errors."""
        self.logger.error(f"Cache error: {error}")

    def _handle_event(self, event):
        """Handle events from the event bus."""
        # Forward relevant events to current page
        if self.current_page and self.current_page in self.pages:
            current_page = self.pages[self.current_page]
            if hasattr(current_page, 'handle_event'):
                current_page.handle_event(event)

    def cleanup_application(self):
        """Clean up resources when application is actually quitting."""
        try:
            self.logger.debug("Starting application cleanup")
            
            # Stop cleanup timer
            if hasattr(self, 'cleanup_update_timer'):
                self.cleanup_update_timer.stop()

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

            # Disconnect any event handlers
            self.event_bus.event_occurred.disconnect(self._handle_event)
            self.cache.initialized.disconnect(self._on_cache_initialized)
            self.cache.error_occurred.disconnect(self._on_cache_error)

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)
            
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
          
    async def _init_cache(self):
        """Initialize caches asynchronously."""
        try:
            await self.cache.initialize(self.playlists_dir)
        except Exception as e:
            self.logger.error(f"Cache initialization failed: {e}")
