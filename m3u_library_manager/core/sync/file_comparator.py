# core/sync/file_comparator.py
import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass

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
        
    def _get_mp3_paths_from_playlist(self, playlist_path: Path) -> Set[Path]:
        """Extract MP3 paths from a playlist file"""
        try:
            self.logger.info(f"Reading playlist: {playlist_path}")
            paths = read_m3u(str(playlist_path))
            mp3_paths = {Path(p) for p in paths if p.lower().endswith('.mp3')}
            self.logger.info(f"Found {len(mp3_paths)} MP3 files in playlist")
            return mp3_paths
        except Exception as e:
            self.logger.error(f"Error reading playlist {playlist_path}: {e}")
            raise
            
    def _convert_to_remote_path(self, local_path: Path, base_dir: Path, remote_base: str) -> str:
        """Convert local path to equivalent remote path"""
        rel_path = local_path.relative_to(base_dir)
        return str(Path(remote_base) / rel_path).replace('\\', '/')
        
    def _convert_to_local_path(self, remote_path: str, remote_base: str, local_base: Path) -> Path:
        """Convert remote path to equivalent local path"""
        rel_path = Path(remote_path).relative_to(Path(remote_base))
        return local_base / rel_path
            
    async def compare_locations(self, 
                              playlist_path: Path,
                              local_base: Path,
                              remote_base: str,
                              progress_callback=None) -> ComparisonResult:
        """
        Compare MP3 files between local and remote locations
        
        Args:
            playlist_path: Path to local playlist file
            local_base: Base directory for local files
            remote_base: Base directory for remote files
            progress_callback: Optional callback for progress updates
            
        Returns:
            ComparisonResult containing sets of missing files
        """
        try:
            # Get local MP3 paths
            self.logger.info("Starting location comparison")
            self.logger.info(f"Local base: {local_base}")
            self.logger.info(f"Remote base: {remote_base}")
            
            local_paths = self._get_mp3_paths_from_playlist(playlist_path)
            if not local_paths:
                self.logger.warning("No MP3 files found in playlist")
                return ComparisonResult(set(), set(), 0)
                
            # Check remote existence
            self.logger.info("Checking remote files...")
            missing_remotely = set()
            total_files = len(local_paths)
            
            for i, local_path in enumerate(local_paths):
                remote_path = self._convert_to_remote_path(local_path, local_base, remote_base)
                self.logger.debug(f"Checking remote: {remote_path}")
                
                if not self.ssh.check_remote_file(remote_path):
                    missing_remotely.add(local_path)
                    self.logger.debug(f"File missing remotely: {remote_path}")
                
                if progress_callback:
                    progress_callback(i / total_files * 50)
                    
            self.logger.info(f"Found {len(missing_remotely)} files missing remotely")
            
            # Get remote playlist
            self.logger.info("Checking local files...")
            remote_playlist = self._convert_to_remote_path(playlist_path, local_base, remote_base)
            temp_playlist = playlist_path.parent / f"temp_{playlist_path.name}"
            
            try:
                self.logger.info(f"Copying remote playlist: {remote_playlist}")
                self.ssh.copy_from_remote(remote_playlist, temp_playlist)
                remote_paths = self._get_mp3_paths_from_playlist(temp_playlist)
            finally:
                if temp_playlist.exists():
                    temp_playlist.unlink()
                    
            # Check local existence
            missing_locally = set()
            remote_total = len(remote_paths)
            
            for i, remote_path in enumerate(remote_paths):
                local_path = self._convert_to_local_path(str(remote_path), remote_base, local_base)
                self.logger.debug(f"Checking local: {local_path}")
                
                if not local_path.exists():
                    missing_locally.add(local_path)
                    self.logger.debug(f"File missing locally: {local_path}")
                
                if progress_callback:
                    progress_callback(50 + (i / remote_total * 50))
                    
            self.logger.info(f"Found {len(missing_locally)} files missing locally")
            self.logger.info("Comparison complete")
            
            return ComparisonResult(
                missing_remotely=missing_remotely,
                missing_locally=missing_locally,
                total_files=total_files
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing locations: {e}", exc_info=True)
            raise