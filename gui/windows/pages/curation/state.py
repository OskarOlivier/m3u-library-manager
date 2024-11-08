# gui/windows/pages/curation/state.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Set
from PyQt6.QtCore import QObject, pyqtSignal
import logging
from utils.m3u.parser import read_m3u

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
    stats_progress = pyqtSignal(int)  # For stats calculation progress
    
    # Status signals
    status_changed = pyqtSignal(str)  # status message
    error_occurred = pyqtSignal(str)  # error message
    progress_updated = pyqtSignal(int)  # progress value
    
    def __init__(self):
        super().__init__()
        self.current_song: Optional[CurrentSong] = None
        self.playlist_counts: Dict[Path, int] = {}
        self.highlighted_playlists: Set[Path] = set()
        self.playlist_manager = None  # Will be set by page
        self.playlists_dir = None  # Will be set by page
        self.logger = logging.getLogger('curation_state')
        
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
        
    def update_progress(self, value: int):
        """Update progress value."""
        self.progress_updated.emit(value)
        
    def collect_unplaylisted(self) -> bool:
        """Create playlist with unplaylisted loved tracks."""
        if not self.playlist_manager:
            return False
            
        try:
            playlisted_tracks = set()
            loved_tracks = set()
            
            # Get all playlisted tracks (excluding Unplaylisted_ playlists)
            for playlist in self.playlists_dir.glob("*.m3u"):
                if (not playlist.name.startswith("Unplaylisted_") and 
                    playlist.name != "Love.bak.m3u"):
                    self.logger.debug(f"Reading playlist: {playlist.name}")
                    paths = read_m3u(str(playlist))
                    self.logger.debug(f"Found {len(paths)} tracks in {playlist.name}")
                    playlisted_tracks.update(paths)
            
            self.logger.info(f"Total tracks in regular playlists: {len(playlisted_tracks)}")
                    
            # Get loved tracks
            loved_playlist = self.playlists_dir / "Love.bak.m3u"
            if not loved_playlist.exists():
                self.report_error("Love.bak.m3u not found")
                return False
                
            loved_tracks = set(read_m3u(str(loved_playlist)))
            self.logger.info(f"Total loved tracks: {len(loved_tracks)}")
            
            # Calculate unplaylisted
            unplaylisted = sorted(loved_tracks - playlisted_tracks)
            self.logger.info(f"Found {len(unplaylisted)} unplaylisted tracks")
            
            if not unplaylisted:
                self.logger.info("No unplaylisted tracks found")
                return False
                
            # Create timestamp-based playlist name
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_playlist = self.playlists_dir / f"Unplaylisted_{timestamp}.m3u"
            
            # Write tracks with UTF-8 encoding
            import codecs
            from utils.m3u.parser import write_m3u
            write_m3u(str(new_playlist), unplaylisted)
            
            # Verify the written file
            try:
                written_tracks = read_m3u(str(new_playlist))
                self.logger.info(f"Successfully wrote {len(written_tracks)} tracks to {new_playlist.name}")
                if len(written_tracks) != len(unplaylisted):
                    raise ValueError("Written track count doesn't match expected")
            except Exception as e:
                self.report_error(f"Failed to verify written playlist: {str(e)}")
                return False
            
            # Try both common Dopamine install locations
            import subprocess
            dopamine_paths = [
                #Path(r"C:\Program Files\Dopamine\Dopamine.exe"),
                Path(r"C:\Program Files (x86)\Dopamine\Dopamine.exe")
            ]
            
            for dopamine_path in dopamine_paths:
                if dopamine_path.exists():
                    self.logger.info(f"Launching Dopamine from: {dopamine_path}")
                    subprocess.Popen([str(dopamine_path), str(new_playlist)])
                    return True
                    
            self.report_error("Dopamine.exe not found in expected locations")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to collect unplaylisted tracks: {e}", exc_info=True)
            self.report_error(f"Failed to collect unplaylisted: {str(e)}")
            return False