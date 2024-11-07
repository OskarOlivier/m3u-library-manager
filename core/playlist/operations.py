# core/playlist/operations.py

from pathlib import Path
from typing import List, Optional, Tuple
from utils.m3u.parser import read_m3u, write_m3u
import logging

class PlaylistOperations:
    """Handles playlist file operations with safety checks"""
    
    def __init__(self, playlist_dir: Path, backup_dir: Path):
        self.playlist_dir = playlist_dir
        self.backup_dir = backup_dir
        self.logger = logging.getLogger('playlist_operations')
        
    def add_song_to_playlist(self, playlist_path: Path, file_path: str) -> Tuple[bool, Optional[int]]:
        """Add a song to playlist with safety checks"""
        try:
            # Create backup
            backup_path = self._create_backup(playlist_path)
            if not backup_path:
                return False, None
                
            # Read current content
            current_paths = read_m3u(str(playlist_path))
            if current_paths is None:
                return False, None
                
            # Only add if not present
            if file_path not in current_paths:
                current_paths.append(file_path)
                write_m3u(str(playlist_path), current_paths)
                
                # Verify write
                new_paths = read_m3u(str(playlist_path))
                if new_paths is None or file_path not in new_paths:
                    self._restore_backup(backup_path, playlist_path)
                    return False, None
                    
            return True, len(current_paths)
            
        except Exception as e:
            self.logger.error(f"Error adding song: {e}")
            return False, None
            
    def remove_song_from_playlist(self, playlist_path: Path, file_path: str) -> Tuple[bool, Optional[int]]:
        """Remove a song from playlist with safety checks"""
        try:
            # Create backup
            backup_path = self._create_backup(playlist_path)
            if not backup_path:
                return False, None
                
            # Read current content
            current_paths = read_m3u(str(playlist_path))
            if current_paths is None:
                return False, None
                
            if file_path in current_paths:
                current_paths.remove(file_path)
                write_m3u(str(playlist_path), current_paths)
                
                # Verify write
                new_paths = read_m3u(str(playlist_path))
                if new_paths is None or file_path in new_paths:
                    self._restore_backup(backup_path, playlist_path)
                    return False, None
                    
            return True, len(current_paths)
            
        except Exception as e:
            self.logger.error(f"Error removing song: {e}")
            return False, None
            
    def get_track_count(self, playlist_path: Path) -> Optional[int]:
        """Get number of tracks in playlist"""
        try:
            paths = read_m3u(str(playlist_path))
            return len(paths) if paths is not None else None
        except Exception as e:
            self.logger.error(f"Error getting track count: {e}")
            return None
            
    def contains_song(self, playlist_path: Path, file_path: str) -> bool:
        """Check if playlist contains specific song"""
        try:
            paths = read_m3u(str(playlist_path))
            return paths is not None and file_path in paths
        except Exception as e:
            self.logger.error(f"Error checking song in playlist: {e}")
            return False
            
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
                return None
                
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
            
    def _restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore playlist from backup"""
        try:
            import shutil
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False