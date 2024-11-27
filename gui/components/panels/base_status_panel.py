# gui/components/panels/base_status_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class StatusPanel(QWidget):
    """Unified status panel for showing operation status and progress."""
    
    def __init__(self, state):
        super().__init__()
        self.state = state
        self._hide_timer = None
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the status panel UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Container for status and progress
        status_container = QVBoxLayout()
        status_container.setSpacing(4)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        status_container.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 2px;
                background-color: #2D2D2D;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 2px;
            }
        """)
        self.progress_bar.setVisible(False)
        status_container.addWidget(self.progress_bar)
        
        layout.addLayout(status_container)
        layout.addStretch()
        
        # Set fixed height for consistent layout
        self.setFixedHeight(50)
        
        # Set background
        self.setStyleSheet("""
            StatusPanel {
                background-color: #202020;
                border-radius: 2px;
            }
        """)
        
    def connect_signals(self):
        """Connect to state signals."""
        if hasattr(self.state, 'status_changed'):
            self.state.status_changed.connect(self.update_status)
        if hasattr(self.state, 'error_occurred'):
            self.state.error_occurred.connect(self.show_error)
        if hasattr(self.state, 'progress_updated'):
            self.state.progress_updated.connect(self.update_progress)
        
    def update_status(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        
    def show_error(self, error: str):
        """Display error message."""
        self.status_label.setText(f"Error: {error}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FF4444;
                background: transparent;
            }
        """)
        self.progress_bar.setVisible(False)
        
    def update_progress(self, value: int):
        """Update progress bar."""
        # Cancel any pending hide timer
        if self._hide_timer and self._hide_timer.isActive():
            self._hide_timer.stop()
        
        if not self.progress_bar.isVisible() and value > 0:
            self.progress_bar.setVisible(True)
            
        self.progress_bar.setValue(value)
        
        # Hide progress when complete with new timer
        if value >= 100:
            self._hide_timer = QTimer(self)
            self._hide_timer.setSingleShot(True)
            self._hide_timer.timeout.connect(self._hide_progress_bar)
            self._hide_timer.start(1000)  # Hide after 1 second

    def _hide_progress_bar(self):
        """Safely hide progress bar if widget still exists."""
        if self.progress_bar and not self.progress_bar.isHidden():
            self.progress_bar.setVisible(False)

    def cleanup(self):
        """Clean up resources."""
        if self._hide_timer:
            self._hide_timer.stop()
            self._hide_timer = None
            
        # Disconnect any connected signals
        if hasattr(self.state, 'status_changed'):
            try:
                self.state.status_changed.disconnect(self.update_status)
            except:
                pass
        if hasattr(self.state, 'error_occurred'):
            try:
                self.state.error_occurred.disconnect(self.show_error)
            except:
                pass
        if hasattr(self.state, 'progress_updated'):
            try:
                self.state.progress_updated.disconnect(self.update_progress)
            except:
                pass