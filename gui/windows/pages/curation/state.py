from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set
from PyQt6.QtCore import QObject, pyqtSignal

@dataclass
class CurrentSong:
    """Currently playing song info."""
    artist: str
    title: str

class CurationState(QObject):
    """State management for curation page."""
    
    # Song signals
    song_changed = pyqtSignal(object)  # Emits CurrentSong
    song_cleared = pyqtSignal()
    
    # Playlist signals
    playlist_updated = pyqtSignal(Path, int)  # playlist_path, new_count
    playlist_highlighted = pyqtSignal(Path, bool)  # playlist_path, highlighted
    playlist_clicked = pyqtSignal(Path)  # playlist_path
    
    # Stats signals
    stats_updated = pyqtSignal(int, int)  # total_tracks, unplaylisted
    
    # Status signals
    status_changed = pyqtSignal(str)  # status message
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.current_song: Optional[CurrentSong] = None
        self.playlist_counts: Dict[Path, int] = {}
        self.highlighted_playlists: Set[Path] = set()
        self.playlist_manager = None  # Will be set by page
        self.playlists_dir = None  # Will be set by page
        
    def set_current_song(self, artist: str, title: str):
        """Update current song."""
        self.current_song = CurrentSong(artist, title)
        self.song_changed.emit(self.current_song)
        
    def clear_current_song(self):
        """Clear current song."""
        self.current_song = None
        self.song_cleared.emit()
        
    def update_stats(self, total: int, unplaylisted: int):
        """Update playlist statistics."""
        self.stats_updated.emit(total, unplaylisted)
        
    def update_playlist(self, playlist: Path, count: int):
        """Update playlist track count."""
        self.playlist_counts[playlist] = count
        self.playlist_updated.emit(playlist, count)
        
    def set_playlist_highlighted(self, playlist: Path, highlighted: bool):
        """Update playlist highlight state."""
        if highlighted:
            self.highlighted_playlists.add(playlist)
        else:
            self.highlighted_playlists.discard(playlist)
        self.playlist_highlighted.emit(playlist, highlighted)
        
    def emit_playlist_clicked(self, playlist: Path):
        """Emit playlist click signal."""
        self.playlist_clicked.emit(playlist)
        
    def set_status(self, message: str):
        """Update status message."""
        self.status_changed.emit(message)
        
    def report_error(self, error: str):
        """Report error condition."""
        self.error_occurred.emit(error)
        self.set_status(f"Error: {error}")
        
    def collect_unplaylisted(self) -> bool:
        """Create playlist with unplaylisted loved tracks."""
        if not self.playlist_manager:
            return False
            
        try:
            playlisted_tracks = set()
            loved_tracks = set()
            
            # Get all playlisted tracks
            for playlist in self.playlists_dir.glob("*.m3u"):
                if playlist.name != "Love.bak.m3u":
                    paths = read_m3u(str(playlist))
                    playlisted_tracks.update(paths)
                    
            # Get loved tracks
            loved_playlist = self.playlists_dir / "Love.bak.m3u"
            if not loved_playlist.exists():
                self.report_error("Love.bak.m3u not found")
                return False
                
            loved_tracks = set(read_m3u(str(loved_playlist)))
            
            # Calculate unplaylisted
            unplaylisted = sorted(loved_tracks - playlisted_tracks)
            if not unplaylisted:
                return False
                
            # Create timestamp-based playlist name
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_playlist = self.playlists_dir / f"Unplaylisted_{timestamp}.m3u"
            
            # Write tracks
            from utils.m3u.parser import write_m3u
            write_m3u(str(new_playlist), unplaylisted)
            
            # Open with Dopamine
            from pathlib import Path
            import subprocess
            dopamine_path = Path(r"C:\Program Files (x86)\Dopamine\dopamine.exe")
            if dopamine_path.exists():
                subprocess.Popen([str(dopamine_path), str(new_playlist)])
                
            return True
            
        except Exception as e:
            self.report_error(f"Failed to collect unplaylisted: {str(e)}")
            return False