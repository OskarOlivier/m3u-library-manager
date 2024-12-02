# system_tray.py

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QObject, QTimer
import logging
from pathlib import Path
import win32gui
import win32con
import win32api
import sys
import traceback

from gui.windows.main_window import MainWindow

class WindowsHotkey:
    """Windows hotkey handler using polling approach."""
    
    def __init__(self):
        self.logger = logging.getLogger('hotkey')
        self.logger.debug("Initializing hotkey handler")
        self.logger.setLevel(logging.INFO)
        self.VK_F = 0x46  # F key
        self.VK_CONTROL = win32con.VK_CONTROL
        self.VK_MENU = win32con.VK_MENU  # ALT
        
    def is_pressed(self) -> bool:
        """Check if the hotkey combination is pressed."""
        try:
            self.logger.debug("Checking hotkey state")
            ctrl_pressed = win32api.GetAsyncKeyState(self.VK_CONTROL) & 0x8000
            alt_pressed = win32api.GetAsyncKeyState(self.VK_MENU) & 0x8000
            f_pressed = win32api.GetAsyncKeyState(self.VK_F) & 0x8000
            
            is_triggered = bool(ctrl_pressed and alt_pressed and f_pressed)
            self.logger.debug(f"Hotkey state - Ctrl: {bool(ctrl_pressed)}, Alt: {bool(alt_pressed)}, F: {bool(f_pressed)}")
            return is_triggered
            
        except Exception as e:
            self.logger.error(f"Error checking hotkey state: {e}", exc_info=True)
            return False

class SystemTrayApp(QObject):
    """Handles system tray icon and hotkey functionality."""
    
    def __init__(self, app: QApplication):
        self.logger = logging.getLogger('system_tray')
        self.logger.debug("Initializing SystemTrayApp")
        
        try:
            super().__init__()  # Initialize QObject first
            self.app = app
            self.window = None
            self.tray_icon = None
            self.last_active_page = None
            self.last_trigger = False
            
            # Initialize hotkey handler
            self.logger.debug("Creating hotkey handler")
            self.hotkey = WindowsHotkey()
            
            # Set up components
            self.logger.debug("Setting up system tray")
            self.setup_system_tray()
            
            # Start hotkey check timer
            self.logger.debug("Starting hotkey check timer")
            self.check_timer = QTimer()
            self.check_timer.timeout.connect(self.check_hotkey)
            self.check_timer.start(100)  # Check every 100ms
            
        except Exception as e:
            self.logger.error(f"Error initializing SystemTrayApp: {e}", exc_info=True)
            raise
        
    def setup_system_tray(self):
        """Initialize system tray icon and menu."""
        try:
            self.logger.debug("Creating system tray icon")
            self.tray_icon = QSystemTrayIcon()
            
            # Use application style icon
            self.logger.debug("Setting tray icon")
            icon = self.app.style().standardIcon(
                self.app.style().StandardPixmap.SP_MediaPlay
            )
            self.tray_icon.setIcon(icon)
            
            # Create menu
            self.logger.debug("Creating tray menu")
            menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show_window)
            menu.addAction(show_action)
            
            menu.addSeparator()
            
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.quit_application)
            menu.addAction(exit_action)
            
            # Set menu and show icon
            self.tray_icon.setContextMenu(menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
            
            # Initial tooltip
            self.tray_icon.setToolTip("M3U Library Manager (Ctrl+Alt+F)")
            
            # Show startup message
            self.logger.debug("Showing startup message")
            self.tray_icon.showMessage(
                "M3U Library Manager",
                "Running in background (Ctrl+Alt+F to show)",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up system tray: {e}", exc_info=True)
            raise
            
    def check_hotkey(self):
        """Check if hotkey is pressed."""
        try:
            is_pressed = self.hotkey.is_pressed()
            if is_pressed and not self.last_trigger:
                self.logger.debug("Hotkey triggered")
                self.toggle_window()
            self.last_trigger = is_pressed
        except Exception as e:
            self.logger.error(f"Error in hotkey check: {e}", exc_info=True)
            
    def on_tray_activated(self, reason):
        """Handle tray icon activation."""
        try:
            self.logger.debug(f"Tray icon activated: {reason}")
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self.show_window()
        except Exception as e:
            self.logger.error(f"Error handling tray activation: {e}", exc_info=True)
            
    def toggle_window(self):
        """Show or hide the window."""
        try:
            self.logger.debug("Toggling window visibility")
            if self.window is None:
                self.show_window()
            else:
                if self.window.isVisible():
                    self.hide_window()
                else:
                    self.show_window()
        except Exception as e:
            self.logger.error(f"Error toggling window: {e}", exc_info=True)
                
    def hide_window(self):
        """Hide the window and remember current page."""
        try:
            self.logger.debug("Hiding window")
            if self.window is not None:
                if hasattr(self.window, 'current_page'):
                    self.last_active_page = self.window.current_page
                    self.logger.debug(f"Saved active page: {self.last_active_page}")
                self.window.hide()
        except Exception as e:
            self.logger.error(f"Error hiding window: {e}", exc_info=True)
            
    def show_window(self):
        """Show the window and restore last active page."""
        try:
            self.logger.debug("Showing window")
            if self.window is None:
                self.logger.debug("Creating new window")
                self.window = MainWindow()
                    
            self._show_initialized_window()
                
        except Exception as e:
            self.logger.error(f"Error showing window: {e}", exc_info=True)
            
    def _show_initialized_window(self):
        """Show the window after initialization is complete."""
        if self.last_active_page and hasattr(self.window, 'switch_page'):
            self.logger.debug(f"Restoring page: {self.last_active_page}")
            self.window.switch_page(self.last_active_page)
                
        self.window.show()
        self.window.setWindowState(self.window.windowState() & ~Qt.WindowState.WindowMinimized)
        self.window.activateWindow()
        self.window.raise_()
        
    def quit_application(self):
        """Clean up and quit the application."""
        try:
            self.logger.debug("Starting application shutdown")
            
            # Stop timer first
            if hasattr(self, 'check_timer'):
                self.logger.debug("Stopping hotkey check timer")
                self.check_timer.stop()
            
            # Clean up window
            if self.window:
                self.logger.debug("Cleaning up window")
                self.window.cleanup_application()
                self.window.close()
                
            # Hide tray icon
            if self.tray_icon:
                self.logger.debug("Hiding tray icon")
                self.tray_icon.hide()
                
            self.logger.debug("Quitting application")
            QApplication.quit()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)
            # Force quit even if cleanup fails
            QApplication.quit()

def main():
    """Main entry point for system tray application."""
    try:
        # Initialize logging first
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('system_tray.log')
            ]
        )
        
        logger = logging.getLogger('main')
        logger.debug("Starting application")
        
        # Create application
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)  # Keep running when window closed
        
        logger.debug("Creating system tray application")
        tray_app = SystemTrayApp(app)
        
        logger.debug("Entering event loop")
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()