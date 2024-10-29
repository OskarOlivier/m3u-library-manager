# gui/windows/playlist_manager.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QLabel, QPushButton,
                           QHeaderView, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont
import win32gui
import keyboard
from pathlib import Path

from core.matching.song_matcher import SongMatcher
from utils.m3u.parser import read_m3u

class PlaylistManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.matcher = SongMatcher()
        self.playlists_dir = Path(r"D:\Music\Dopamine\Playlists")
        self.music_dir = Path(r"E:\Albums")
        
        # Window setup
        self.setWindowTitle("Playlist Manager")
        self.setGeometry(100, 100, 1200, 800)  # Large window
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Current song info
        self.song_info = QLabel()
        self.song_info.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.song_info)
        
        # Playlists table
        self.playlists_table = QTableWidget()
        self.playlists_table.setColumnCount(4)
        self.playlists_table.setHorizontalHeaderLabels([
            "Playlist", "Tracks", "Has Current", "Actions"
        ])
        self.playlists_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.playlists_table)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_current_song)
        self.update_timer.start(1000)  # Check every second
        
        # Register global hotkey
        keyboard.add_hotkey('ctrl+alt+p', self.toggle_visibility)
        
        self.current_song = None
        self.refresh_playlists()
        self.hide()  # Start hidden

    def refresh_playlists(self):
        """Update the playlists table"""
        self.playlists_table.setRowCount(0)
        
        for playlist_path in sorted(self.playlists_dir.glob("*.m3u")):
            row = self.playlists_table.rowCount()
            self.playlists_table.insertRow(row)
            
            # Playlist name
            name_item = QTableWidgetItem(playlist_path.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.playlists_table.setItem(row, 0, name_item)
            
            # Track count
            try:
                tracks = read_m3u(str(playlist_path))
                count_item = QTableWidgetItem(str(len(tracks)))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.playlists_table.setItem(row, 1, count_item)
            except:
                self.playlists_table.setItem(row, 1, QTableWidgetItem("Error"))
            
            # Has current song (will be updated in check_current_song)
            has_current = QTableWidgetItem("")
            has_current.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playlists_table.setItem(row, 2, has_current)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            
            add_btn = QPushButton("Add")
            add_btn.clicked.connect(lambda checked, p=playlist_path: self.add_to_playlist(p))
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, p=playlist_path: self.remove_from_playlist(p))
            
            actions_layout.addWidget(add_btn)
            actions_layout.addWidget(remove_btn)
            self.playlists_table.setCellWidget(row, 3, actions_widget)

    def check_current_song(self):
        """Check currently playing song and update UI"""
        try:
            window_title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
            parsed = self.matcher.parse_window_title(window_title)
            
            if parsed and (parsed != self.current_song):
                self.current_song = parsed
                artist, title = parsed
                self.song_info.setText(f"Current: {artist} - {title}")
                
                # Find matching files and playlists
                files, playlists = self.matcher.find_matches(
                    title=title,
                    artist=artist,
                    music_dir=str(self.music_dir),
                    playlists_dir=str(self.playlists_dir)
                )
                
                # Update "Has Current" column
                for row in range(self.playlists_table.rowCount()):
                    playlist_name = self.playlists_table.item(row, 0).text()
                    has_current = QTableWidgetItem("û" if playlist_name in playlists else "")
                    has_current.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    has_current.setFlags(has_current.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.playlists_table.setItem(row, 2, has_current)
                    
        except Exception as e:
            print(f"Error checking current song: {e}")

    def add_to_playlist(self, playlist_path):
        """Add current song to playlist"""
        if not self.current_song:
            return
            
        artist, title = self.current_song
        files, _ = self.matcher.find_matches(
            title=title,
            artist=artist,
            music_dir=str(self.music_dir)
        )
        
        if files:
            try:
                current_paths = read_m3u(str(playlist_path))
                file_str = str(files[0])
                
                if file_str not in current_paths:
                    current_paths.append(file_str)
                    with open(playlist_path, 'w', encoding='utf-8') as f:
                        for path in current_paths:
                            f.write(f"{path}\n")
                    
                self.refresh_playlists()
                
            except Exception as e:
                print(f"Error adding to playlist: {e}")

    def remove_from_playlist(self, playlist_path):
        """Remove current song from playlist"""
        if not self.current_song:
            return
            
        artist, title = self.current_song
        files, _ = self.matcher.find_matches(
            title=title,
            artist=artist,
            music_dir=str(self.music_dir)
        )
        
        if files:
            try:
                current_paths = read_m3u(str(playlist_path))
                file_str = str(files[0])
                
                if file_str in current_paths:
                    current_paths.remove(file_str)
                    with open(playlist_path, 'w', encoding='utf-8') as f:
                        for path in current_paths:
                            f.write(f"{path}\n")
                    
                self.refresh_playlists()
                
            except Exception as e:
                print(f"Error removing from playlist: {e}")

    def toggle_visibility(self):
        """Toggle window visibility on Ctrl+Alt+P"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.refresh_playlists()
