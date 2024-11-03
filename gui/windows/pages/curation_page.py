# gui/windows/pages/curation_page.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from pathlib import Path

from gui.windows.pages import BasePage
from core.matching.window_handler import WindowHandler
from core.playlist.playlist_manager import PlaylistManager

class PlaylistClickHandler(QObject):
    """Signal handler for playlist clicks"""
    clicked = pyqtSignal(Path)

class PlaylistItem(QLabel):
    """Interactive playlist item with Windows 10 styling"""
    def __init__(self, playlist_path: Path, track_count: int, click_handler: PlaylistClickHandler, parent=None):
        super().__init__(parent)
        self.playlist_path = playlist_path
        self.click_handler = click_handler
        self.track_count = track_count
        self.highlighted = False
        
        # Create container widget
        self.container = QFrame(self)
        
        # Create layout for the container
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        # Create labels for playlist name and track count
        self.name_label = QLabel(playlist_path.stem, self.container)
        self.count_label = QLabel(str(track_count), self.container)
        
        # Set font for both labels
        font = QFont("Segoe UI", 11)
        self.name_label.setFont(font)
        self.count_label.setFont(font)
        
        # Add labels to layout
        self.layout.addWidget(self.name_label, 1)  # 1 for stretch
        self.layout.addWidget(self.count_label)
        
        # Set up outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.addWidget(self.container)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(50)
        self.update_style()
        
    def update_display(self):
        """Update playlist display"""
        try:
            from utils.m3u.parser import read_m3u
            self.track_count = len(read_m3u(str(self.playlist_path)))
            self.count_label.setText(str(self.track_count))
        except Exception:
            self.track_count = 0
            self.count_label.setText("0")
        self.update_style()
        
    def update_style(self):
        # Windows 10 style for container
        container_style = f"""
            QFrame {{
                background-color: {("#0078D4" if self.highlighted else "#2D2D2D")};
                border: none;
                border-radius: 2px;
            }}
        """
        
        self.container.setStyleSheet(container_style)
        
        # Style for name label - Windows 10 font
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 4px;
            }
        """)
        
        # Style for count label - Right aligned
        self.count_label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 4px;
                min-width: 40px;
                qproperty-alignment: 'AlignRight | AlignVCenter';
            }
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_handler.clicked.emit(self.playlist_path)

class CurationPage(BasePage):
    def __init__(self):
        self.playlists_dir = Path(r"D:\Music\Dopamine\Playlists")
        self.music_dir = Path(r"E:\Albums")
        self.playlist_manager = PlaylistManager(self.music_dir, self.playlists_dir)
        self.playlist_items = {}
        self.current_song = None
        self.click_handler = PlaylistClickHandler()
        super().__init__()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Main container
        main_container = QWidget(self)
        main_container.setStyleSheet("""
            QWidget {
                background-color: #202020;
            }
        """)
        layout.addWidget(main_container)
        
        # Create layout for main container
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Current song info
        song_container = QWidget(main_container)
        song_layout = QVBoxLayout(song_container)
        song_layout.setContentsMargins(0, 0, 0, 0)
        
        self.song_info = QLabel("No song playing")
        self.song_info.setFont(QFont("Segoe UI", 11))
        self.song_info.setStyleSheet("color: white;")
        song_layout.addWidget(self.song_info)
        
        main_layout.addWidget(song_container)
        
        # Grid container
        grid_container = QWidget(main_container)
        
        # Create grid layout
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        
        # Wrap in scroll area with Windows 10 styling
        scroll = QScrollArea(main_container)
        scroll.setWidget(grid_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 16px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                min-height: 20px;
                border-radius: 3px;
                margin: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7F7F7F;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        main_layout.addWidget(scroll)
        
        # Connect click handler
        self.click_handler.clicked.connect(self.on_playlist_click)
        
        # Initial playlist load
        self.refresh_playlists()
        
        # Update timer for song detection
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_current_song)
        self.update_timer.start(1000)

    def on_playlist_click(self, playlist_path: Path):
        """Handle playlist click events"""
        if not self.current_song:
            return
            
        artist, title = self.current_song
        item = self.playlist_items[playlist_path]
        success, new_count = self.playlist_manager.toggle_song_in_playlist(
            playlist_path,
            artist,
            title,
            not item.highlighted
        )
        
        if success:
            item.highlighted = not item.highlighted
            item.track_count = new_count if new_count is not None else item.track_count
            item.update_display()

    def refresh_playlists(self):
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Add playlists to grid
        playlists = sorted(self.playlists_dir.glob("*.m3u"))
        cols = 4
        
        for i, playlist_path in enumerate(playlists):
            try:
                from utils.m3u.parser import read_m3u
                track_count = len(read_m3u(str(playlist_path)))
            except Exception:
                track_count = 0
                
            item = PlaylistItem(playlist_path, track_count, self.click_handler)
            self.playlist_items[playlist_path] = item
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(item, row, col)

    def check_current_song(self):
        """Check for the currently playing song"""
        try:
            song_info = WindowHandler.get_current_song()
            if song_info and (song_info != self.current_song):
                self.current_song = song_info
                artist, title = song_info
                self.song_info.setText(f"Current: {artist} - {title}")
                
                playlists = self.playlist_manager.get_song_playlists(artist, title)
                
                for path, item in self.playlist_items.items():
                    item.highlighted = path.name in playlists
                    item.update_style()
                    
        except Exception as e:
            print(f"Error checking current song: {e}")