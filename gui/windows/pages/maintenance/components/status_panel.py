# gui/windows/pages/maintenance/components/status_panel.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class StatusPanel(QWidget):
    """Panel for showing operation status and progress."""
    
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
        # Status updates
        self.state.status_changed.connect(self.update_status)
        self.state.error_occurred.connect(self.show_error)
        
        # Progress updates
        self.state.progress_updated.connect(self.update_progress)
        
        # Operation states
        self.state.operation_started.connect(self.on_operation_started)
        self.state.operation_completed.connect(self.on_operation_completed)
        
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
        
        # Show error dialog for serious errors
        QMessageBox.critical(
            self,
            "Operation Failed",
            f"An error occurred:\n{error}",
            QMessageBox.StandardButton.Ok
        )
        
    def update_progress(self, value: int):
        """Update progress bar."""
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        
        # Hide progress when complete
        if value >= 100:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
            
    def on_operation_started(self, operation: str):
        """Handle operation start."""
        self.update_status(f"Running {operation}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
    def on_operation_completed(self, operation: str, success: bool):
        """Handle operation completion."""
        if success:
            self.update_status(f"{operation} completed successfully")
            self.progress_bar.setValue(100)
        else:
            self.show_error(f"{operation} failed")
        
        # Hide progress after delay
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))