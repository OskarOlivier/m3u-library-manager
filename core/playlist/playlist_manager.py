# core/playlist/playlist_manager.py

from pathlib import Path
from typing import Optional, Tuple, List, Dict
import logging

from core.matching.song_matcher import SongMatcher
from core.common.file_utils import search_music_directory
from core.playlist.operations import PlaylistOperations

class PlaylistManager:
    """Manages playlist operations and song toggling"""
    
    def __init__(self, music_dir: Path, playlists_dir: Path, backup_dir: Path):
        """
        Initialize PlaylistManager.
        
        Args:
            music_dir: Base directory for music files
            playlists_dir: Directory containing playlists
            backup_dir: Directory for playlist backups
        """
        self.music_dir = music_dir
        self.playlists_dir = playlists_dir
        self.matcher = SongMatcher()
        self.operations = PlaylistOperations(playlists_dir, backup_dir)
        self.logger = logging.getLogger('playlist_manager')
        
    def toggle_song_in_playlist(self, 
                              playlist_path: Path, 
                              artist: str, 
                              title: str, 
                              include: bool) -> Tuple[bool, Optional[int]]:
        """
        Toggle song presence in playlist.
        
        Args:
            playlist_path: Path to playlist file
            artist: Artist name
            title: Song title
            include: True to add, False to remove
            
        Returns:
            Tuple of (success, new_track_count)
        """
        try:
            # Find matching files
            files = search_music_directory(
                artist=artist,
                title=title,
                music_dir=self.music_dir
            )
            
            if not files:
                self.logger.warning(f"No matching files found for {artist} - {title}")
                return False, None
                
            file_str = str(files[0])
            
            if include:
                success, count = self.operations.add_song_to_playlist(playlist_path, file_str)
            else:
                success, count = self.operations.remove_song_from_playlist(playlist_path, file_str)
                
            if success:
                self.logger.info(
                    f"Successfully {'added to' if include else 'removed from'} "
                    f"{playlist_path.name}, new count: {count}"
                )
                return True, count
                
            return False, None
            
        except Exception as e:
            self.logger.error(f"Error toggling song in playlist: {e}")
            return False, None
            
    def get_song_playlists(self, artist: str, title: str) -> List[str]:
        """
        Get list of playlist names containing the specified song.
        
        Args:
            artist: Artist name
            title: Song title
            
        Returns:
            List of playlist names containing the song
        """
        try:
            _, playlists = self.matcher.find_matches(
                title=title,
                artist=artist,
                music_dir=str(self.music_dir),
                playlists_dir=str(self.playlists_dir)
            )
            return playlists
        except Exception as e:
            self.logger.error(f"Error getting song playlists: {e}")
            return []
            
    def get_all_playlists(self) -> List[Tuple[Path, int]]:
        """
        Get all playlists and their track counts.
        
        Returns:
            List of tuples containing (playlist_path, track_count)
        """
        try:
            playlists = []
            for path in sorted(self.playlists_dir.glob("*.m3u")):
                count = self.operations.get_track_count(path) or 0
                playlists.append((path, count))
            return playlists
        except Exception as e:
            self.logger.error(f"Error getting playlists: {e}")
            return []
            
    def contains_song(self, playlist_path: Path, file_path: Path) -> bool:
        """
        Check if playlist contains specific song.
        
        Args:
            playlist_path: Path to playlist
            file_path: Path to song file
            
        Returns:
            True if song is in playlist
        """
        try:
            return self.operations.contains_song(playlist_path, str(file_path))
        except Exception as e:
            self.logger.error(f"Error checking song in playlist: {e}")
            return False