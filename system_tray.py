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

from gui.windows.main_window import MainWindow
from core.events.event_bus import EventBus  # Add this import too here

class WindowsHotkey:
    """Windows hotkey handler using polling approach."""
    
    def __init__(self):
        self.VK_F = 0x46  # F key
        self.VK_CONTROL = win32con.VK_CONTROL
        self.VK_MENU = win32con.VK_MENU  # ALT
        
    def is_pressed(self) -> bool:
        """Check if the hotkey combination is pressed."""
        try:
            ctrl_pressed = win32api.GetAsyncKeyState(self.VK_CONTROL) & 0x8000
            alt_pressed = win32api.GetAsyncKeyState(self.VK_MENU) & 0x8000
            f_pressed = win32api.GetAsyncKeyState(self.VK_F) & 0x8000
            return bool(ctrl_pressed and alt_pressed and f_pressed)
        except Exception as e:
            logging.error(f"Error checking hotkey state: {e}")
            return False

class SystemTrayApp(QObject):
    """Handles system tray icon and hotkey functionality."""
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.window = None
        self.tray_icon = None
        self.hotkey = WindowsHotkey()
        self.last_trigger = False
        
        self.logger = logging.getLogger('system_tray')
        
        # Set up components
        self.setup_system_tray()
        
        # Start hotkey check timer
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_hotkey)
        self.check_timer.start(100)  # Check every 100ms
        
        self.last_active_page = None
        
    def setup_system_tray(self):
        """Initialize system tray icon and menu."""
        try:
            # Create tray icon
            self.tray_icon = QSystemTrayIcon(self)
            
            # Use application style icon
            icon = self.app.style().standardIcon(
                self.app.style().StandardPixmap.SP_MediaPlay
            )
            self.tray_icon.setIcon(icon)
            
            # Create menu
            menu = QMenu()
            
            show_action = QAction("Show", menu)
            show_action.triggered.connect(self.show_window)
            menu.addAction(show_action)
            
            menu.addSeparator()
            
            exit_action = QAction("Exit", menu)
            exit_action.triggered.connect(self.quit_application)
            menu.addAction(exit_action)
            
            # Set menu and show icon
            self.tray_icon.setContextMenu(menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
            
            # Initial tooltip
            self.tray_icon.setToolTip("M3U Library Manager (Ctrl+Alt+F)")
            
            # Show startup message
            self.tray_icon.showMessage(
                "M3U Library Manager",
                "Running in background (Ctrl+Alt+F to show)",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up system tray: {e}")
            raise
            
    def check_hotkey(self):
        """Check if hotkey is pressed."""
        try:
            is_pressed = self.hotkey.is_pressed()
            if is_pressed and not self.last_trigger:
                self.toggle_window()
            self.last_trigger = is_pressed
        except Exception as e:
            self.logger.error(f"Error checking hotkey: {e}")
            
    def on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
            
    def toggle_window(self):
        """Show or hide the window."""
        if self.window is None:
            self.show_window()
        else:
            if self.window.isVisible():
                self.hide_window()
            else:
                self.show_window()
                
    def hide_window(self):
        """Hide the window and remember current page."""
        if self.window is not None:
            if hasattr(self.window, 'current_page'):
                self.last_active_page = self.window.current_page
            self.window.hide()
            
    def show_window(self):
        """Show the window and restore last active page."""
        if self.window is None:
            self.window = MainWindow()
            
        if self.last_active_page and hasattr(self.window, 'switch_page'):
            self.window.switch_page(self.last_active_page)
            
        self.window.show()
        self.window.setWindowState(self.window.windowState() & ~Qt.WindowState.WindowMinimized)
        self.window.activateWindow()
        self.window.raise_()
        
    def quit_application(self):
        """Clean up and quit the application."""
        try:
            if self.window:
                self.window.close()
            self.check_timer.stop()
            if self.tray_icon:
                self.tray_icon.hide()
            self.app.quit()
        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            self.app.quit()  # Force quit even if cleanup fails

            
def main():
    """Main entry point for system tray application."""
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when window closed
    
    # Create system tray
    tray_app = SystemTrayApp(app)
    
    # Run event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()