# gui/windows/pages/sync/components/status_panel.py

"""Status and progress panel implementation."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..state import SyncPageState

class StatusPanel(QWidget):
    """Panel showing status and progress information."""
    
    def __init__(self, state: SyncPageState):
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
        
        # Set background for the entire panel
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
        
        # Analysis state
        self.state.analysis_started.connect(lambda p: self.on_operation_started(f"Analyzing {p.name}..."))
        self.state.analysis_completed.connect(lambda p, _: self.on_operation_completed(f"Analysis complete for {p.name}"))
        self.state.analysis_all_started.connect(lambda: self.on_operation_started("Analyzing all playlists..."))
        self.state.analysis_all_completed.connect(lambda: self.on_operation_completed("All playlists analyzed"))
        
        # Sync state
        self.state.sync_started.connect(lambda op: self.on_operation_started(f"Syncing files ({op})..."))
        self.state.sync_completed.connect(lambda: self.on_operation_completed("Sync complete"))
        
    def update_status(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
        
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
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        
        # If complete, hide after a delay
        if value >= 100:
            self.schedule_progress_hide()
            
    def schedule_progress_hide(self):
        """Schedule progress bar to be hidden."""
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
        
    def on_operation_started(self, message: str):
        """Handle operation start."""
        self.update_status(message)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
    def on_operation_completed(self, message: str):
        """Handle operation completion."""
        self.update_status(message)
        self.progress_bar.setValue(100)
        self.schedule_progress_hide()
        
    def resizeEvent(self, event):
        """Handle resize events to maintain layout."""
        super().resizeEvent(event)
        # Ensure progress bar width matches label
        self.progress_bar.setMaximumWidth(self.status_label.width())