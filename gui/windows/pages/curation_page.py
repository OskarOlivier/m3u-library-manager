# gui/windows/pages/curation_page.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QDateTime
from PyQt6.QtGui import QFont
from pathlib import Path
import logging
import winreg
import subprocess
from typing import Optional

from gui.windows.pages import BasePage
from core.matching.window_handler import WindowHandler
from core.playlist import PlaylistManager
from gui.widgets import PlaylistItem, ClickHandler
from utils.m3u.parser import read_m3u, write_m3u

class StatsWidget(QWidget):
    """Widget for displaying library statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Create a stretch to push everything to the right
        layout.addStretch()
        
        # Stats labels
        self.total_tracks = QLabel("Total unique tracks: 0")
        self.total_tracks.setFont(QFont("Segoe UI", 10))
        self.total_tracks.setStyleSheet("color: #999999;")
        
        self.unplaylisted = QLabel("Loved not in playlist: 0")
        self.unplaylisted.setFont(QFont("Segoe UI", 10))
        self.unplaylisted.setStyleSheet("color: #999999;")
        
        # Collect button (renamed from "Collect Loved" to "Collect")
        self.collect_button = QPushButton("Collect")
        self.collect_button.setFont(QFont("Segoe UI", 10))
        self.collect_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #1982D4;
            }
            QPushButton:pressed {
                background-color: #106EBE;
            }
        """)
        
        # Add widgets to layout (after the stretch)
        layout.addWidget(self.total_tracks)
        layout.addWidget(self.unplaylisted)
        layout.addWidget(self.collect_button)
        
    def update_stats(self, total: int, unplaylisted: int):
        """Update statistics display"""
        self.total_tracks.setText(f"Total tracks: {total:,}")
        self.unplaylisted.setText(f"Loved not in playlist: {unplaylisted:,}")

class CurationPage(BasePage):
    def __init__(self):
        self.playlists_dir = Path(r"D:\Music\Dopamine\Playlists")
        self.music_dir = Path(r"E:\Albums")
        self.playlist_manager = PlaylistManager(self.music_dir, self.playlists_dir)
        self.playlist_items = {}
        self.current_song = None
        self.click_handler = ClickHandler()
        self.logger = logging.getLogger('curation_page')
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
        
        # Stats bar container
        stats_container = QWidget(main_container)
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)
        
        # Current song info with fixed width
        self.song_info = QLabel("No song playing")
        self.song_info.setFont(QFont("Segoe UI", 11))
        self.song_info.setStyleSheet("color: white;")
        self.song_info.setMinimumWidth(200)  # Ensure minimum width for song info
        stats_layout.addWidget(self.song_info)
        
        # Stats widget (right aligned)
        self.stats_widget = StatsWidget()
        stats_layout.addWidget(self.stats_widget, 1)  # Give stats widget stretch priority
        
        main_layout.addWidget(stats_container)
        
        # Connect collect button
        self.stats_widget.collect_button.clicked.connect(self.collect_unplaylisted)
        
        # Grid container
        grid_container = QWidget(main_container)
        
        # Create grid layout
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        
        # Wrap in scroll area
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

    def calculate_stats(self) -> tuple[int, int]:
        """Calculate total tracks and unplaylisted loved tracks"""
        try:
            # Get all unique tracks from regular playlists
            playlisted_tracks = set()
            for playlist in self.playlists_dir.glob("*.m3u"):
                # Skip both "Love.bak.m3u" and any playlist starting with "Unplaylisted_"
                if playlist.name == "Love.bak.m3u" or playlist.name.startswith("Unplaylisted_"):
                    continue
                paths = read_m3u(str(playlist))
                playlisted_tracks.update(paths)
                    
            # Get loved tracks
            loved_tracks = set()
            loved_playlist = self.playlists_dir / "Love.bak.m3u"
            if loved_playlist.exists():
                loved_tracks = set(read_m3u(str(loved_playlist)))
                
            # Calculate unplaylisted
            unplaylisted = loved_tracks - playlisted_tracks
                
            return len(playlisted_tracks), len(unplaylisted)
            
        except Exception as e:
            self.logger.error(f"Error calculating stats: {e}")
            return 0, 0

    def collect_unplaylisted(self):
        """Create playlist with loved tracks not in other playlists"""
        try:
            from datetime import datetime
            
            dopamine_path = r"C:\Program Files (x86)\Dopamine\dopamine.exe"
            
            # Get all playlisted tracks
            playlisted_tracks = set()
            for playlist in self.playlists_dir.glob("*.m3u"):
                if playlist.name != "Love.bak.m3u":
                    paths = read_m3u(str(playlist))
                    playlisted_tracks.update(paths)
                    
            # Get loved tracks
            loved_playlist = self.playlists_dir / "Love.bak.m3u"
            if not loved_playlist.exists():
                self.logger.warning("Love.bak.m3u not found")
                return
                
            loved_tracks = set(read_m3u(str(loved_playlist)))
            
            # Get unplaylisted tracks
            unplaylisted = sorted(loved_tracks - playlisted_tracks)
            
            if not unplaylisted:
                self.logger.info("No unplaylisted tracks found")
                return
                
            # Create new playlist
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_playlist = self.playlists_dir / f"Unplaylisted_{timestamp}.m3u"
            
            # Write tracks
            write_m3u(str(new_playlist), unplaylisted)
            self.logger.info(f"Created new playlist: {new_playlist}")
            
            # Open with Dopamine
            try:
                subprocess.Popen([dopamine_path, str(new_playlist)])
                self.logger.info("Launched Dopamine with new playlist")
            except subprocess.SubprocessError as e:
                self.logger.error(f"Failed to launch Dopamine: {e}")
            
            # Refresh display
            self.refresh_playlists()
            
        except Exception as e:
            self.logger.error(f"Error collecting unplaylisted: {e}", exc_info=True)

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
            
            # Update stats after playlist modification
            total, unplaylisted = self.calculate_stats()
            self.stats_widget.update_stats(total, unplaylisted)

    def refresh_playlists(self):
        """Refresh playlist grid and stats"""
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        self.playlist_items.clear()
        
        # Add playlists to grid
        playlists = sorted(p for p in self.playlists_dir.glob("*.m3u")
                          if p.name != "Love.bak.m3u")
        cols = 4
        
        for i, playlist_path in enumerate(playlists):
            try:
                track_count = len(read_m3u(str(playlist_path)))
                item = PlaylistItem(playlist_path, track_count, self.click_handler)
                self.playlist_items[playlist_path] = item
                row = i // cols
                col = i % cols
                self.grid_layout.addWidget(item, row, col)
            except Exception as e:
                self.logger.error(f"Error adding playlist {playlist_path}: {e}")
                
        # Update stats
        total, unplaylisted = self.calculate_stats()
        self.stats_widget.update_stats(total, unplaylisted)

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

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