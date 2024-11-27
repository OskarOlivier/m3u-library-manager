# core/sync/sync_operations.py

from pathlib import Path
import logging
import asyncio
from typing import Dict, Set, Optional, Callable
from datetime import datetime
import tempfile

from utils.m3u.parser import read_m3u, write_m3u, _normalize_path, _denormalize_path
from utils.m3u.path_utils import verify_library_path
from .ssh_handler import SSHHandler
from .backup_manager import BackupManager

class SyncOperationError(Exception):
    """Custom exception for sync operation failures."""
    pass

class SyncOperations:
    """
    Handles playlist sync operations. Only modifies m3u playlist files,
    never copies, moves, or modifies the actual media files. All operations
    are purely path-based operations within playlist files.
    """
    
    def __init__(self, ssh_handler: SSHHandler, backup_manager: BackupManager,
                 local_base: Path, remote_base: str):
        self.ssh = ssh_handler
        self.backup = backup_manager
        self.local_base = local_base
        self.remote_base = remote_base
        self.logger = logging.getLogger('sync_operations')
        
    async def add_to_remote(self, files: Set[Path], playlist_path: Path,
                           progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Add file paths to remote playlist. Only modifies the playlist file,
        does not transfer any media files.
        
        Args:
            files: Set of file paths to add to playlist
            playlist_path: Path to the playlist file
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: Success status
        """
        try:
            if not files:
                self.logger.warning("No files provided to add to remote")
                return False

            self.logger.info(f"Adding {len(files)} paths to remote playlist: {playlist_path.name}")
            remote_playlist = f"{self.remote_base}/{playlist_path.name}"
            temp_path = Path(tempfile.gettempdir()) / f"temp_{playlist_path.name}"

            # Get current remote content
            self.logger.debug(f"Fetching remote playlist: {remote_playlist}")
            remote_exists = self.ssh.copy_from_remote(remote_playlist, temp_path)
            current_paths = read_m3u(str(temp_path)) if remote_exists else []
            self.logger.debug(f"Current remote paths count: {len(current_paths) if current_paths else 0}")

            # Verify all paths match library format
            for file_path in files:
                if error := verify_library_path(str(file_path)):
                    raise SyncOperationError(f"Invalid path format: {file_path} - {error}")

            # Preserve case from local paths
            local_paths = read_m3u(str(playlist_path))
            case_map = {_normalize_path(str(p)).lower(): str(p) for p in local_paths} if local_paths else {}
            
            # Add new paths while preserving case
            new_paths = set(current_paths) if current_paths else set()
            for file_path in files:
                normalized_path = _normalize_path(str(file_path))
                lower_path = normalized_path.lower()
                if lower_path in case_map:
                    new_paths.add(case_map[lower_path])
                else:
                    new_paths.add(normalized_path)

            # Sort and write to temp file
            sorted_paths = sorted(new_paths)
            write_m3u(str(temp_path), sorted_paths, use_absolute_paths=False)

            # Copy to remote
            if not self.ssh.copy_to_remote(temp_path, remote_playlist):
                raise SyncOperationError("Failed to update remote playlist")

            # Verify remote update
            verify_temp = Path(tempfile.gettempdir()) / f"verify_{playlist_path.name}"
            if not self.ssh.copy_from_remote(remote_playlist, verify_temp):
                raise SyncOperationError("Failed to verify remote playlist update")

            verify_paths = read_m3u(str(verify_temp))
            if set(verify_paths) != set(sorted_paths):
                raise SyncOperationError("Remote playlist verification failed")

            # Cleanup temp files
            for temp_file in [temp_path, verify_temp]:
                if temp_file.exists():
                    temp_file.unlink()

            self.logger.info("Successfully added paths to remote playlist")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add paths to remote: {e}", exc_info=True)
            return False
            
    async def add_to_local(self, files: Set[Path], playlist_path: Path,
                          progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Add file paths to local playlist. Only modifies the playlist file,
        does not transfer any media files.
        
        Args:
            files: Set of file paths to add to playlist
            playlist_path: Path to the playlist file
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: Success status
        """
        try:
            if not files:
                self.logger.warning("No files provided to add locally")
                return False

            self.logger.info(f"Adding {len(files)} paths to local playlist: {playlist_path.name}")
            
            # Create backup
            backup_path = self.backup.create_backup(playlist_path)
            if not backup_path:
                raise SyncOperationError("Failed to create backup")

            # Read current content
            current_paths = read_m3u(str(playlist_path))
            if current_paths is None:
                raise SyncOperationError("Failed to read local playlist")

            # Add new paths
            new_paths = set(current_paths)
            new_paths.update(_normalize_path(str(f)) for f in files)
            sorted_paths = sorted(new_paths)

            # Write updated playlist
            write_m3u(str(playlist_path), sorted_paths)

            # Verify update
            verify_paths = read_m3u(str(playlist_path))
            if set(verify_paths) != set(sorted_paths):
                self.logger.error("Local playlist verification failed")
                self._restore_backup(backup_path, playlist_path)
                return False

            if progress_callback:
                progress_callback(100)

            self.logger.info("Successfully added paths to local playlist")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add paths locally: {e}", exc_info=True)
            return False

    async def remove_from_remote(self, files: Set[Path], playlist_path: Path,
                               progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Remove file paths from remote playlist. Only modifies the playlist file,
        does not modify any media files.
        
        Args:
            files: Set of file paths to remove from playlist
            playlist_path: Path to the playlist file
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: Success status
        """
        try:
            if not files:
                self.logger.warning("No files provided to remove from remote")
                return False

            self.logger.info(f"Removing {len(files)} paths from remote playlist: {playlist_path.name}")
            remote_playlist = f"{self.remote_base}/{playlist_path.name}"
            temp_path = Path(tempfile.gettempdir()) / f"temp_{playlist_path.name}"

            # Get current remote content
            if not self.ssh.copy_from_remote(remote_playlist, temp_path):
                raise SyncOperationError("Failed to fetch remote playlist")

            current_paths = read_m3u(str(temp_path))
            if current_paths is None:
                raise SyncOperationError("Failed to read remote playlist")

            # Remove paths (case-insensitive)
            files_to_remove = {_normalize_path(str(f)).lower() for f in files}
            new_paths = [p for p in current_paths 
                        if _normalize_path(p).lower() not in files_to_remove]

            # Write back to temp file
            write_m3u(str(temp_path), new_paths, use_absolute_paths=False)

            # Copy to remote
            if not self.ssh.copy_to_remote(temp_path, remote_playlist):
                raise SyncOperationError("Failed to update remote playlist")

            # Verify removal
            verify_temp = Path(tempfile.gettempdir()) / f"verify_{playlist_path.name}"
            if not self.ssh.copy_from_remote(remote_playlist, verify_temp):
                raise SyncOperationError("Failed to verify remote playlist update")

            verify_paths = read_m3u(str(verify_temp))
            if set(verify_paths) != set(new_paths):
                raise SyncOperationError("Remote playlist verification failed")

            # Cleanup
            for temp_file in [temp_path, verify_temp]:
                if temp_file.exists():
                    temp_file.unlink()

            if progress_callback:
                progress_callback(100)

            self.logger.info("Successfully removed paths from remote playlist")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove paths from remote: {e}", exc_info=True)
            return False

    async def remove_from_local(self, files: Set[Path], playlist_path: Path,
                              progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Remove file paths from local playlist. Only modifies the playlist file,
        does not modify any media files.
        
        Args:
            files: Set of file paths to remove from playlist
            playlist_path: Path to the playlist file
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: Success status
        """
        try:
            if not files:
                self.logger.warning("No files provided to remove locally")
                return False

            self.logger.info(f"Removing {len(files)} paths from local playlist: {playlist_path.name}")

            # Create backup
            backup_path = self.backup.create_backup(playlist_path)
            if not backup_path:
                raise SyncOperationError("Failed to create backup")

            # Read current content
            current_paths = read_m3u(str(playlist_path))
            if current_paths is None:
                raise SyncOperationError("Failed to read local playlist")

            # Remove paths (case-insensitive)
            files_to_remove = {_normalize_path(str(f)).lower() for f in files}
            new_paths = [p for p in current_paths 
                        if _normalize_path(p).lower() not in files_to_remove]

            # Write updated playlist
            write_m3u(str(playlist_path), new_paths)

            # Verify removal
            verify_paths = read_m3u(str(playlist_path))
            if set(verify_paths) != set(new_paths):
                self.logger.error("Local playlist verification failed")
                self._restore_backup(backup_path, playlist_path)
                return False

            if progress_callback:
                progress_callback(100)

            self.logger.info("Successfully removed paths from local playlist")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove paths locally: {e}", exc_info=True)
            return False

    async def sync_playlist(self, playlist_path: Path,
                          add_to_remote: Set[Path] = None,
                          add_to_local: Set[Path] = None,
                          remove_from_remote: Set[Path] = None,
                          remove_from_local: Set[Path] = None,
                          progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Sync playlist by modifying m3u files only. Never copies or moves media files.
        Maintains original filepath case sensitivity.
        
        Args:
            playlist_path: Path to the playlist file
            add_to_remote: Paths to add to remote playlist
            add_to_local: Paths to add to local playlist
            remove_from_remote: Paths to remove from remote playlist
            remove_from_local: Paths to remove from local playlist
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Starting playlist sync for {playlist_path.name}")
            
            # Initialize empty sets
            add_to_remote = add_to_remote or set()
            add_to_local = add_to_local or set()
            remove_from_remote = remove_from_remote or set()
            remove_from_local = remove_from_local or set()

            # Create backup before any modifications
            backup_path = self.backup.create_backup(playlist_path)
            if not backup_path:
                raise SyncOperationError("Failed to create backup")

            if progress_callback:
                progress_callback(10)

            # Track progress for each operation
            steps = sum(bool(x) for x in [add_to_remote, add_to_local, 
                                        remove_from_remote, remove_from_local])
            if steps == 0:
                return True

            current_step = 0
            
            def update_progress(step_progress: float):
                if progress_callback:
                    total_progress = ((current_step / steps) * 90) + (step_progress * 0.9 / steps)
                    progress_callback(int(10 + total_progress))

            # Handle each operation
            if add_to_remote:
                current_step += 1
                if not await self.add_to_remote(add_to_remote, playlist_path, update_progress):
                    raise SyncOperationError("Failed to add paths to remote")

            if add_to_local:
                current_step += 1
                if not await self.add_to_local(add_to_local, playlist_path, update_progress):
                    raise SyncOperationError("Failed to add paths locally")

            if remove_from_remote:
                current_step += 1
                if not await self.remove_from_remote(remove_from_remote, playlist_path, update_progress):
                    raise SyncOperationError("Failed to remove paths from remote")

            if remove_from_local:
                current_step += 1
                if not await self.remove_from_local(remove_from_local, playlist_path, update_progress):
                    raise SyncOperationError("Failed to remove paths locally")

            if progress_callback:
                progress_callback(100)

            self.logger.info("Playlist sync completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Sync failed: {e}", exc_info=True)
            if 'backup_path' in locals():
                self._restore_backup(backup_path, playlist_path)
            return False

    def _restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore from backup after failed operation."""
        try:
            self.logger.info(f"Restoring backup for {target_path.name}")
            return self.backup.restore_backup(backup_path, target_path)
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False