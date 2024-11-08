# gui/components/status_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class StatusPanel(QWidget):
    """Unified status panel for showing operation status and progress."""
    
    def __init__(self, state):
        super().__init__()
        self.state = state
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
        if not self.progress_bar.isVisible() and value > 0:
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        
        # Hide progress when complete
        if value >= 100:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))