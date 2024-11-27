# core/playlist/playlist_manager.py

from pathlib import Path
from typing import Optional, Tuple, List, Dict
import logging

from core.matching.playlist_matcher import PlaylistMatcher
from core.playlist.operations import PlaylistOperations
from utils.m3u.parser import _normalize_path

class PlaylistManager:
    """
    High-level manager for playlist operations with path normalization.
    Coordinates between UI actions and low-level operations.
    """
    
    def __init__(self, music_dir: Path, playlists_dir: Path, backup_dir: Path):
        self.music_dir = music_dir
        self.playlists_dir = playlists_dir
        self.matcher = PlaylistMatcher()
        self.operations = PlaylistOperations(playlists_dir, backup_dir)
        
        # Set up logging
        self.logger = logging.getLogger('playlist_manager')
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
       
    def toggle_song_in_playlist(self, 
                              playlist_path: Path, 
                              file_path: str, 
                              include: bool) -> Tuple[bool, Optional[int]]:
        """
        Toggle a song's presence in a playlist.
        
        Args:
            playlist_path: Path to the playlist file
            file_path: Path to the music file (absolute or relative)
            include: True to add, False to remove
            
        Returns:
            Tuple[bool, Optional[int]]: (success, new_track_count)
        """
        try:
            # Normalize file path
            normalized_path = _normalize_path(file_path)
            
             # Check current state with normalized path
            current_state = self.operations.contains_song(playlist_path, normalized_path)
 
            # Only perform operation if state will change
            if current_state != include:
                if include:
                    success, count = self.operations.add_song_to_playlist(playlist_path, normalized_path)
                else:
                    success, count = self.operations.remove_song_from_playlist(playlist_path, normalized_path)
                    
                if success:
                    return True, count
                    
                self.logger.error(f"Failed to {'add' if include else 'remove'} song")
                return False, None
            
            # No change needed - get current count
            count = self.operations.get_track_count(playlist_path)
            return True, count
            
        except Exception as e:
            self.logger.error(f"Error toggling song in playlist: {e}", exc_info=True)
            return False, None
        
    def get_song_playlists(self, filepath: str) -> List[str]:
        """
        Get playlists containing a specific file.
        
        Args:
            filepath: Path to the file to search for (absolute or relative)
            
        Returns:
            List[str]: Names of playlists containing the file
        """
        try:
            if not filepath:
                self.logger.warning("No file path provided")
                return []
            
            # Normalize path before searching    
            normalized_path = _normalize_path(filepath)
                
            playlists = self.matcher.find_playlists_for_file(
                normalized_path,
                str(self.playlists_dir)
            )
            
            self.logger.debug(f"Found in playlists: {playlists}")
            return playlists
            
        except Exception as e:
            self.logger.error(f"Error getting song playlists: {e}", exc_info=True)
            return []
            
    def get_all_playlists(self) -> List[Tuple[Path, int]]:
        """Get all playlists with their track counts."""
        try:
            playlists = []
            for path in sorted(self.playlists_dir.glob("*.m3u")):
                count = self.operations.get_track_count(path) or 0
                playlists.append((path, count))
                
            self.logger.debug(f"Found {len(playlists)} playlists")
            return playlists
            
        except Exception as e:
            self.logger.error(f"Error getting playlists: {e}", exc_info=True)
            return []
            
    def create_new_playlist(self, name: str, file_paths: List[str]) -> Optional[Path]:
        """
        Create a new playlist with the given files.
        
        Args:
            name: Name for the new playlist (without .m3u extension)
            file_paths: List of file paths to include (absolute or relative)
            
        Returns:
            Path to created playlist if successful, None otherwise
        """
        try:
            # Ensure .m3u extension
            if not name.endswith('.m3u'):
                name += '.m3u'
                
            playlist_path = self.playlists_dir / name
            
            # Normalize all paths
            normalized_paths = [_normalize_path(path) for path in file_paths]
            self.logger.debug(f"Creating playlist {name} with {len(normalized_paths)} files")
            
            # Create playlist using operations class for consistency
            success, _ = self.operations.write_new_playlist(playlist_path, normalized_paths)
            if success:
                self.logger.info(f"Successfully created playlist: {name}")
                return playlist_path
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating playlist: {e}", exc_info=True)
            return None