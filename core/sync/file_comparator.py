# core/sync/file_comparator.py

import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional, Callable
from dataclasses import dataclass

from utils.m3u.parser import read_m3u, _normalize_path, _denormalize_path
from utils.m3u.path_utils import verify_library_path
from .ssh_handler import SSHHandler

@dataclass
class ComparisonResult:
    """Stores the results of comparing local and remote locations"""
    missing_remotely: Set[Path]    # Files that need to be uploaded
    missing_locally: Set[Path]     # Files that need to be downloaded
    total_files: int              # Total number of files in playlist
    exists_remotely: bool = True   # Whether the playlist exists on remote
    has_invalid_paths: bool = False  # Whether any paths don't match library format

class FileComparator:
    """Compares files between local and remote locations using normalized paths"""
    
    def __init__(self, ssh_handler: SSHHandler):
        self.ssh = ssh_handler
        
        # Set up logging
        self.logger = logging.getLogger('file_comparator')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

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
        Compare playlist contents between local and remote locations.
        Uses normalized paths for consistent comparison.
        
        Args:
            playlist_path: Path to the playlist file
            local_base: Base path for local music library
            remote_base: Base path for remote music library
            progress_callback: Optional callback for progress updates
            
        Returns:
            ComparisonResult containing comparison details
            
        Raises:
            FileNotFoundError: If playlist doesn't exist
            Exception: For other errors during comparison
        """
        try:
            self.logger.info("Starting playlist comparison")
            self.logger.debug(f"Playlist: {playlist_path}")
            self.logger.debug(f"Local base: {local_base}")
            self.logger.debug(f"Remote base: {remote_base}")

            has_invalid_paths = False
            
            # Quick check for remote playlist
            if not self.check_remote_playlist(playlist_path.name):
                self.logger.warning(f"Remote playlist not found: {playlist_path.name}")
                return ComparisonResult(
                    missing_remotely=set(),
                    missing_locally=set(),
                    total_files=0,
                    exists_remotely=False,
                    has_invalid_paths=False
                )
            
            # Get local playlist content (already normalized by read_m3u)
            local_paths = read_m3u(str(playlist_path))
            if not local_paths:
                self.logger.warning("No files found in local playlist")
                return ComparisonResult(set(), set(), 0, True, False)
                
            if progress_callback:
                progress_callback(25)

            # Verify local paths match library format
            for path in local_paths:
                if error := verify_library_path(path):
                    self.logger.warning(f"Invalid path format: {path} - {error}")
                    has_invalid_paths = True
                
            # Get remote playlist content
            remote_playlist_path = f"{remote_base}/{playlist_path.name}"
            temp_playlist = Path(tempfile.gettempdir()) / f"temp_{playlist_path.name}"
            
            try:
                self.logger.info(f"Copying remote playlist: {remote_playlist_path}")
                success = self.ssh.copy_from_remote(remote_playlist_path, temp_playlist)
                
                if not success:
                    self.logger.warning(f"Remote playlist not found: {playlist_path.name}")
                    return ComparisonResult(
                        missing_remotely={Path(local_base) / p for p in local_paths},
                        missing_locally=set(),
                        total_files=len(local_paths),
                        exists_remotely=False,
                        has_invalid_paths=has_invalid_paths
                    )
                
                # Get normalized remote paths
                remote_paths = read_m3u(str(temp_playlist))
                if remote_paths is None:
                    raise Exception("Failed to read remote playlist")
                    
                self.logger.debug(f"Found {len(remote_paths)} paths in remote playlist")
                
            finally:
                if temp_playlist.exists():
                    temp_playlist.unlink()
                    
            if progress_callback:
                progress_callback(50)
            
            # Convert normalized paths to sets for comparison
            local_set = set(local_paths)
            remote_set = set(remote_paths)
            
            # Find differences using normalized paths
            missing_remotely = {
                Path(local_base) / p
                for p in local_set - remote_set
            }
            
            missing_locally = {
                Path(local_base) / p
                for p in remote_set - local_set
            }
            
            # Log results
            self.logger.info(f"Found {len(missing_remotely)} files missing remotely")
            self.logger.info(f"Found {len(missing_locally)} files missing locally")
            self.logger.info(f"Has invalid paths: {has_invalid_paths}")
            
            if missing_remotely:
                self.logger.debug("Files missing remotely:")
                for path in missing_remotely:
                    self.logger.debug(f"  {path}")
                    
            if missing_locally:
                self.logger.debug("Files missing locally:")
                for path in missing_locally:
                    self.logger.debug(f"  {path}")
            
            if progress_callback:
                progress_callback(100)
            
            return ComparisonResult(
                missing_remotely=missing_remotely,
                missing_locally=missing_locally,
                total_files=len(local_paths),
                exists_remotely=True,
                has_invalid_paths=has_invalid_paths
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing locations: {e}", exc_info=True)
            raise

    async def verify_files(self, 
                          files: Set[Path], 
                          progress_callback: Optional[Callable[[float], None]] = None) -> Set[Path]:
        """
        Verify existence of files on remote system.
        
        Args:
            files: Set of file paths to verify
            progress_callback: Optional callback for progress updates
            
        Returns:
            Set of files that exist remotely
        """
        try:
            self.logger.info(f"Verifying {len(files)} files on remote system")
            existing_files = set()
            total_files = len(files)
            
            for i, file_path in enumerate(files, 1):
                if progress_callback:
                    progress = int((i / total_files) * 100)
                    progress_callback(progress)
                    
                # Use normalized path for remote check
                normalized_path = _normalize_path(str(file_path))
                remote_path = f"{self.ssh.credentials.remote_path}/{normalized_path}"
                
                # Check file existence without downloading
                if await self._check_remote_file(remote_path):
                    existing_files.add(file_path)
                    self.logger.debug(f"File exists remotely: {file_path}")
                else:
                    self.logger.debug(f"File missing remotely: {file_path}")
                    
                # Allow other operations to process
                await asyncio.sleep(0)
                
            self.logger.info(f"Found {len(existing_files)} files existing remotely")
            return existing_files
            
        except Exception as e:
            self.logger.error(f"Error verifying files: {e}")
            return set()

    async def _check_remote_file(self, remote_path: str) -> bool:
        """Check if a file exists on the remote system."""
        try:
            # Use 'test' command to check file existence
            result = await self.ssh.run_command(f'test -f "{remote_path}"')
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking remote file: {e}")
            return False
            
    def normalize_paths_for_remote(self, playlist_path: Path) -> List[str]:
        """
        Read playlist and normalize paths for remote system.
        
        Args:
            playlist_path: Path to playlist file
            
        Returns:
            List of normalized paths for remote system
        """
        try:
            paths = read_m3u(str(playlist_path))
            if paths is None:
                raise ValueError("Failed to read playlist")
                
            # Normalize all paths for remote system
            normalized = []
            for path in paths:
                # Convert Windows path to POSIX format
                posix_path = Path(path).as_posix()
                # Remove local base path prefix
                if posix_path.startswith(self.local_base.as_posix()):
                    posix_path = posix_path[len(str(self.local_base))+1:]
                normalized.append(posix_path)
                
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing paths: {e}")