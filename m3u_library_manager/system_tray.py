from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QObject, QTimer
import win32gui
import win32con
import win32api
import sys
import os

from gui.windows.main_window import MainWindow

class WindowsHotkey:
    """
    Windows hotkey handler using a simpler polling approach
    """
    def __init__(self):
        # Virtual key codes
        self.VK_F = 0x46  # F key
        self.VK_CONTROL = win32con.VK_CONTROL
        self.VK_MENU = win32con.VK_MENU  # ALT
        
    def is_pressed(self):
        """Check if the hotkey combination is pressed"""
        try:
            # Check if both Ctrl and Alt are pressed
            ctrl_pressed = win32api.GetAsyncKeyState(self.VK_CONTROL) & 0x8000
            alt_pressed = win32api.GetAsyncKeyState(self.VK_MENU) & 0x8000
            f_pressed = win32api.GetAsyncKeyState(self.VK_F) & 0x8000
            
            return bool(ctrl_pressed and alt_pressed and f_pressed)
        except Exception:
            return False

class SystemTrayApp(QObject):
    """Handles system tray icon and hotkey functionality"""
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.window = None
        self.tray_icon = None
        self.hotkey = WindowsHotkey()
        self.last_trigger = False  # Prevent multiple triggers
        
        # Set up components
        self.setup_system_tray()
        
        # Start hotkey check timer
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_hotkey)
        self.check_timer.start(100)  # Check every 100ms
        
    def setup_system_tray(self):
        """Initialize system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app.style().standardIcon(self.app.style().StandardPixmap.SP_MediaPlay))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Show startup message
        self.tray_icon.showMessage(
            "M3U Library Manager",
            "Running in background (Ctrl+Alt+F to show)",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def check_hotkey(self):
        """Check if hotkey is pressed"""
        try:
            is_pressed = self.hotkey.is_pressed()
            if is_pressed and not self.last_trigger:
                self.show_window()
            self.last_trigger = is_pressed
        except Exception as e:
            print(f"Error checking hotkey: {e}")
    
    def show_window(self):
        """Show or create the main window"""
        if self.window is None:
            self.window = MainWindow()
        
        if self.window.isHidden():
            self.window.show()
        else:
            self.window.setWindowState(self.window.windowState() & ~Qt.WindowState.WindowMinimized)
            self.window.activateWindow()
            self.window.raise_()
    
    def quit_application(self):
        """Clean up and quit the application"""
        if self.window:
            self.window.close()
        self.check_timer.stop()
        self.tray_icon.hide()
        self.app.quit()