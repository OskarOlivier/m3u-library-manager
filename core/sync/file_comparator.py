# core/sync/file_comparator.py

import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional, Callable
from dataclasses import dataclass
import tempfile
from utils.m3u.parser import read_m3u
from .ssh_handler import SSHHandler

@dataclass
class ComparisonResult:
    """Stores the results of comparing local and remote locations"""
    missing_remotely: Set[Path]
    missing_locally: Set[Path]
    total_files: int
    exists_remotely: bool = True

class FileComparator:
    """Compares files between local and remote locations"""
    
    def __init__(self, ssh_handler: SSHHandler):
        self.ssh = ssh_handler
        self.logger = logging.getLogger('file_comparator')

    def check_remote_playlist(self, playlist_name: str) -> bool:
        """
        Quickly check if a playlist exists on the remote system.
        
        Args:
            playlist_name: Name of playlist file
            
        Returns:
            bool: True if playlist exists remotely
        """
        remote_path = f"{self.ssh.credentials.remote_path}/{playlist_name}"
        temp_path = Path(tempfile.gettempdir()) / f"temp_{playlist_name}"
        
        try:
            self.logger.debug(f"Checking remote playlist: {remote_path}")
            success = self.ssh.copy_from_remote(remote_path, temp_path)
            self.logger.debug(f"Remote check result: {success}")
            
            if temp_path.exists():
                self.logger.debug("Cleaning up temporary file")
                temp_path.unlink()
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error checking remote playlist: {e}")
            return False
            
    async def compare_locations(self, 
                              playlist_path: Path,
                              local_base: Path,
                              remote_base: str,
                              progress_callback: Optional[Callable[[float], None]] = None) -> ComparisonResult:
        """
        Compare playlist contents between local and remote locations
        """
        try:
            self.logger.info("Starting playlist comparison")
            
            # Quick check for remote playlist
            if not self.check_remote_playlist(playlist_path.name):
                self.logger.warning(f"Remote playlist not found: {playlist_path.name}")
                return ComparisonResult(
                    missing_remotely=set(),
                    missing_locally=set(),
                    total_files=0,
                    exists_remotely=False
                )
            
            # Get local playlist content
            local_paths = self._get_normalized_paths(playlist_path)
            if not local_paths:
                self.logger.warning("No MP3 files found in local playlist")
                return ComparisonResult(set(), set(), 0)
                
            if progress_callback:
                progress_callback(25)
                
            # Get remote playlist content
            remote_playlist_path = f"/media/CHIA/Music/{playlist_path.name}"
            temp_playlist = Path(tempfile.gettempdir()) / f"temp_{playlist_path.name}"
            
            try:
                self.logger.info(f"Copying remote playlist: {remote_playlist_path}")
                success = self.ssh.copy_from_remote(remote_playlist_path, temp_playlist)
                
                if not success:
                    self.logger.warning(f"Remote playlist not found: {playlist_path.name}")
                    return ComparisonResult(
                        missing_remotely=set(Path('E:/Albums').joinpath(p.replace('/', '\\')) 
                                           for p in local_paths),
                        missing_locally=set(),
                        total_files=len(local_paths),
                        exists_remotely=False
                    )
                
                remote_paths = self._get_normalized_paths(temp_playlist, is_remote=True)
                
            finally:
                if temp_playlist.exists():
                    temp_playlist.unlink()
                    
            if progress_callback:
                progress_callback(50)
            
            # Compare paths
            missing_remotely = {
                Path('E:/Albums').joinpath(p.replace('/', '\\'))
                for p in local_paths - remote_paths
            }
            
            missing_locally = {
                Path('E:/Albums').joinpath(p.replace('/', '\\'))
                for p in remote_paths - local_paths
            }
            
            # Log results
            self.logger.info(f"Found {len(missing_remotely)} files missing remotely")
            self.logger.info(f"Found {len(missing_locally)} files missing locally")
            
            if progress_callback:
                progress_callback(100)
            
            return ComparisonResult(
                missing_remotely=missing_remotely,
                missing_locally=missing_locally,
                total_files=len(local_paths),
                exists_remotely=True
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing locations: {e}", exc_info=True)
            raise

    def _normalize_path(self, path: str) -> str:
        """Convert path to normalized format for comparison"""
        # Remove base path prefix and convert to forward slashes
        path = path.replace('E:\\Albums\\', '').replace('\\', '/')
        return path.lower()  # Case-insensitive comparison
        
    def _get_normalized_paths(self, playlist_path: Path, is_remote: bool = False) -> Set[str]:
        """Get normalized paths from playlist file"""
        try:
            self.logger.info(f"Reading playlist: {playlist_path}")
            paths = read_m3u(str(playlist_path))
            
            # Sort paths for easier comparison
            paths.sort()
            
            # Normalize paths
            normalized_paths = {
                self._normalize_path(p)
                for p in paths 
                if p.lower().endswith('.mp3')
            }
            
            count = len(normalized_paths)
            location = "remote" if is_remote else "local"
            self.logger.info(f"Found {count} MP3 files in {location} playlist")
            
            return normalized_paths
            
        except Exception as e:
            self.logger.error(f"Error reading playlist {playlist_path}: {e}")
            raise