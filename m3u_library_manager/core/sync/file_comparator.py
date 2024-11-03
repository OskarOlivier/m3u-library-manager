# core/sync/file_comparator.py

import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass
import tempfile

from .ssh_handler import SSHHandler
from utils.m3u.parser import read_m3u

@dataclass
class ComparisonResult:
    """Stores the results of comparing local and remote locations"""
    missing_remotely: Set[Path]
    missing_locally: Set[Path]
    total_files: int

class FileComparator:
    """Compares files between local and remote locations"""
    
    def __init__(self, ssh_handler: SSHHandler):
        self.ssh = ssh_handler
        self.logger = logging.getLogger('file_comparator')
        
    def _normalize_local_path(self, path: str) -> str:
        """Convert local path to normalized format"""
        # Remove E:\Albums\ prefix and convert to forward slashes
        normalized = path.replace('E:\\Albums\\', '').replace('\\', '/')
        return normalized
        
    def _get_normalized_paths(self, playlist_path: Path) -> Set[str]:
        """Get normalized paths from playlist file"""
        try:
            self.logger.info(f"Reading playlist: {playlist_path}")
            paths = read_m3u(str(playlist_path))
            normalized_paths = {
                self._normalize_local_path(p)
                for p in paths 
                if p.lower().endswith('.mp3')
            }
            self.logger.info(f"Found {len(normalized_paths)} MP3 files in playlist")
            return normalized_paths
        except Exception as e:
            self.logger.error(f"Error reading playlist {playlist_path}: {e}")
            raise
            
    def _get_remote_playlist_path(self, playlist_name: str) -> str:
        """Get the remote path for a playlist"""
        return f"/media/CHIA/Music/{playlist_name}"
            
    async def compare_locations(self, 
                              playlist_path: Path,
                              local_base: Path,
                              remote_base: str,
                              progress_callback=None) -> ComparisonResult:
        """
        Compare playlist contents between local and remote locations
        """
        try:
            self.logger.info("Starting playlist comparison")
            
            # Get local playlist content
            local_paths = self._get_normalized_paths(playlist_path)
            if not local_paths:
                self.logger.warning("No MP3 files found in local playlist")
                return ComparisonResult(set(), set(), 0)
                
            if progress_callback:
                progress_callback(25)
                
            # Get remote playlist content
            remote_playlist_path = self._get_remote_playlist_path(playlist_path.name)
            temp_playlist = Path(tempfile.gettempdir()) / f"temp_{playlist_path.name}"
            
            try:
                self.logger.info(f"Copying remote playlist: {remote_playlist_path}")
                self.ssh.copy_from_remote(remote_playlist_path, temp_playlist)
                remote_paths = self._get_normalized_paths(temp_playlist)
            finally:
                if temp_playlist.exists():
                    temp_playlist.unlink()
                    
            if progress_callback:
                progress_callback(50)
            
            # Convert paths to Path objects for return value
            missing_remotely = {Path('E:/Albums').joinpath(p) for p in local_paths - remote_paths}
            missing_locally = {Path('E:/Albums').joinpath(p) for p in remote_paths - local_paths}
            
            self.logger.info(f"Found {len(missing_remotely)} files missing remotely")
            self.logger.info(f"Found {len(missing_locally)} files missing locally")
            
            if progress_callback:
                progress_callback(100)
            
            return ComparisonResult(
                missing_remotely=missing_remotely,
                missing_locally=missing_locally,
                total_files=len(local_paths)
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing locations: {e}", exc_info=True)
            raise