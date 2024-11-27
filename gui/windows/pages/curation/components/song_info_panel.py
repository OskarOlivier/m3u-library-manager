# gui/windows/pages/curation/components/song_info_panel.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class SongInfoPanel(QWidget):
    """Panel showing current song and status"""
    
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.status_timer = QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self._reset_status)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.info_label = QLabel("No song playing")
        self.info_label.setFont(QFont("Segoe UI", 11))
        self.info_label.setStyleSheet("color: white;")
        self.info_label.setMinimumWidth(200)
        
        layout.addWidget(self.info_label)
        layout.addStretch()
        
    def connect_signals(self):
        """Connect to state signals"""
        self.state.song_changed.connect(self._on_song_changed)
        self.state.song_cleared.connect(self._on_song_cleared)
        self.state.status_changed.connect(self._on_status_changed)
        self.state.error_occurred.connect(self._on_error)
        
    def _on_song_changed(self, song):
        """Handle song change"""
        self.info_label.setText(f"Current: {song.artist} - {song.title}")
        
    def _on_song_cleared(self):
        """Handle song cleared"""
        self.info_label.setText("No song playing")
        
    def _on_status_changed(self, status):
        """Handle status change - ignore to keep current song display"""
        pass
        
    def _on_error(self, error):
        """Handle error - ignore to keep current song display"""
        pass
        
    def _reset_status(self):
        """Reset to current song display"""
        if self.state.current_song:
            song = self.state.current_song
            self.info_label.setText(f"Current: {song.artist} - {song.title}")
        else:
            self.info_label.setText("No song playing")
            
    def cleanup(self):
        """Clean up resources"""
        self.status_timer.stop()