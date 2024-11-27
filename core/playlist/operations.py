# core/playlist/operations.py

from pathlib import Path
from typing import List, Optional, Tuple
from utils.m3u.parser import read_m3u, write_m3u, _normalize_path, _denormalize_path
import logging

class PlaylistOperations:
    """Handles playlist file operations with safety checks and path normalization"""
    
    def __init__(self, playlist_dir: Path, backup_dir: Path):
        self.playlist_dir = playlist_dir
        self.backup_dir = backup_dir
        
        # Set up logger
        self.logger = logging.getLogger('playlist_operations')
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
    def add_song_to_playlist(self, playlist_path: Path, file_path: str) -> Tuple[bool, Optional[int]]:
        """
        Add a song to playlist with safety checks.
        
        Args:
            playlist_path: Path to playlist file
            file_path: Path to music file (can be absolute or relative)
            
        Returns:
            (success, new_track_count)
        """
        try:
            # Normalize input path
            normalized_path = _normalize_path(file_path)
            
            # Verify playlist path
            if not playlist_path.exists():
                self.logger.error(f"Playlist not found: {playlist_path}")
                return False, None
                
            # Create backup
            backup_path = self._create_backup(playlist_path)
            if not backup_path:
                self.logger.error("Failed to create backup")
                return False, None
            
            # Read current content
            current_paths = read_m3u(str(playlist_path))
            if current_paths is None:
                self.logger.error("Failed to read playlist")
                return False, None
                
            # Check if file already exists (using normalized paths)
            if normalized_path in current_paths:
                return True, len(current_paths)
            
            # Add normalized path
            current_paths.append(normalized_path)
            
            # Write updated content
            write_m3u(str(playlist_path), current_paths)
            
            # Verify write
            verification_paths = read_m3u(str(playlist_path))
            if verification_paths is None or normalized_path not in verification_paths:
                self.logger.error("Failed to verify write operation")
                self._restore_backup(backup_path, playlist_path)
                return False, None
                    
            return True, len(current_paths)
            
        except Exception as e:
            self.logger.error(f"Error adding song: {e}", exc_info=True)
            if 'backup_path' in locals():
                self._restore_backup(backup_path, playlist_path)
            return False, None
            
    def remove_song_from_playlist(self, playlist_path: Path, file_path: str) -> Tuple[bool, Optional[int]]:
        """
        Remove a song from playlist with safety checks.
        
        Args:
            playlist_path: Path to playlist file
            file_path: Path to music file (can be absolute or relative)
            
        Returns:
            (success, new_track_count)
        """
        try:
            # Normalize input path
            normalized_path = _normalize_path(file_path)
            
            # Verify playlist path
            if not playlist_path.exists():
                self.logger.error(f"Playlist not found: {playlist_path}")
                return False, None
                
            # Create backup
            backup_path = self._create_backup(playlist_path)
            if not backup_path:
                self.logger.error("Failed to create backup")
                return False, None
                
            # Read current content
            current_paths = read_m3u(str(playlist_path))
            if current_paths is None:
                self.logger.error("Failed to read playlist")
                return False, None
                
            # Check if file exists and remove it
            if normalized_path not in current_paths:
                self.logger.debug("File not found in playlist")
                return True, len(current_paths)
                
            # Remove path while preserving order
            new_paths = [p for p in current_paths if p != normalized_path]
            
            # Write updated content
            write_m3u(str(playlist_path), new_paths)
            
            # Verify write
            verification_paths = read_m3u(str(playlist_path))
            if verification_paths is None or normalized_path in verification_paths:
                self.logger.error("Failed to verify write operation")
                self._restore_backup(backup_path, playlist_path)
                return False, None
                    
            return True, len(new_paths)
            
        except Exception as e:
            self.logger.error(f"Error removing song: {e}", exc_info=True)
            if 'backup_path' in locals():
                self._restore_backup(backup_path, playlist_path)
            return False, None
            
    def contains_song(self, playlist_path: Path, file_path: str) -> bool:
        """
        Check if playlist contains specific song using normalized paths.
        
        Args:
            playlist_path: Path to playlist file
            file_path: Path to music file (can be absolute or relative)
            
        Returns:
            bool: True if file is in playlist
        """
        try:
            # Read and normalize paths
            paths = read_m3u(str(playlist_path))
            if paths is None:
                self.logger.error("Failed to read playlist")
                return False
                
            normalized_check = _normalize_path(file_path)
            
            # Direct comparison of normalized paths
            contains = normalized_check in paths
            
            return contains
            
        except Exception as e:
            self.logger.error(f"Error checking song in playlist: {e}")
            return False
            
    def get_track_count(self, playlist_path: Path) -> Optional[int]:
        """Get number of tracks in playlist"""
        try:
            paths = read_m3u(str(playlist_path))
            count = len(paths) if paths is not None else None
            return count
        except Exception as e:
            self.logger.error(f"Error getting track count: {e}")
            return None
            
    def _create_backup(self, playlist_path: Path) -> Optional[Path]:
        """Create backup of playlist file"""
        try:
            import datetime
            import shutil
            
            # Create backup filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{playlist_path.stem}_{timestamp}{playlist_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Ensure backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup
            shutil.copy2(playlist_path, backup_path)
            
            # Verify backup
            if not backup_path.exists():
                self.logger.error("Backup file not created")
                return None
                
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
            
    def _restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore playlist from backup"""
        try:
            import shutil
            self.logger.debug(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
                
    def write_new_playlist(self, playlist_path: Path, normalized_paths: List[str]) -> Tuple[bool, Optional[int]]:
        """
        Create a new playlist file with the given normalized paths.
        
        Args:
            playlist_path: Path where to create the playlist
            normalized_paths: List of already normalized paths to include
            
        Returns:
            Tuple[bool, Optional[int]]: (success, track_count)
        """
        try:
            self.logger.debug(f"Creating new playlist: {playlist_path}")
            
            if playlist_path.exists():
                self.logger.error("Playlist already exists")
                return False, None
                
            # Write the playlist
            write_m3u(str(playlist_path), normalized_paths)
            
            # Verify write
            verification_paths = read_m3u(str(playlist_path))
            if not verification_paths:
                self.logger.error("Failed to verify new playlist")
                return False, None
                
            count = len(verification_paths)
            self.logger.debug(f"Successfully created playlist with {count} tracks")
            return True, count
            
        except Exception as e:
            self.logger.error(f"Failed to create playlist: {e}", exc_info=True)
            return False, None