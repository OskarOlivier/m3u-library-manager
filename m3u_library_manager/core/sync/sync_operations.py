# core/sync/sync_operations.py
from pathlib import Path
from typing import List, Set, Callable, Optional
from datetime import datetime
import logging
import shutil
from .ssh_handler import SSHHandler
from .backup_manager import BackupManager

class SyncOperations:
    """Handles sync operations between local and remote locations"""
    
    def __init__(self, 
                 ssh_handler: SSHHandler,
                 backup_manager: BackupManager,
                 local_base: Path,
                 remote_base: str):
        self.ssh = ssh_handler
        self.backup = backup_manager
        self.local_base = local_base
        self.remote_base = remote_base
        
    def _convert_to_remote_path(self, local_path: Path) -> str:
        """Convert local path to remote path"""
        rel_path = local_path.relative_to(self.local_base)
        return str(Path(self.remote_base) / rel_path).replace('\\', '/')
        
    async def add_to_remote(self, 
                           files: Set[Path],
                           progress_callback: Optional[Callable[[float], None]] = None) -> None:
        """Copy files to remote location"""
        try:
            total = len(files)
            for i, local_path in enumerate(files):
                if not local_path.exists():
                    logging.warning(f"Local file not found: {local_path}")
                    continue
                    
                remote_path = self._convert_to_remote_path(local_path)
                self.ssh.copy_to_remote(local_path, remote_path)
                
                if progress_callback:
                    progress_callback((i + 1) / total * 100)
                    
        except Exception as e:
            logging.error(f"Error adding files to remote: {e}")
            raise
            
    async def add_to_local(self,
                          files: Set[Path],
                          progress_callback: Optional[Callable[[float], None]] = None) -> None:
        """Copy files from remote location"""
        try:
            total = len(files)
            for i, local_path in enumerate(files):
                remote_path = self._convert_to_remote_path(local_path)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                self.ssh.copy_from_remote(remote_path, local_path)
                
                if progress_callback:
                    progress_callback((i + 1) / total * 100)
                    
        except Exception as e:
            logging.error(f"Error adding files to local: {e}")
            raise
            
    async def remove_from_remote(self,
                               files: Set[Path],
                               progress_callback: Optional[Callable[[float], None]] = None) -> None:
        """Delete files from remote location"""
        try:
            total = len(files)
            for i, local_path in enumerate(files):
                remote_path = self._convert_to_remote_path(local_path)
                self.ssh.delete_remote_file(remote_path)
                
                if progress_callback:
                    progress_callback((i + 1) / total * 100)
                    
        except Exception as e:
            logging.error(f"Error removing files from remote: {e}")
            raise
            
    async def remove_from_local(self,
                              files: Set[Path],
                              progress_callback: Optional[Callable[[float], None]] = None) -> None:
        """Delete files from local location"""
        try:
            total = len(files)
            for i, local_path in enumerate(files):
                if local_path.exists():
                    local_path.unlink()
                    
                if progress_callback:
                    progress_callback((i + 1) / total * 100)
                    
        except Exception as e:
            logging.error(f"Error removing files from local: {e}")
            raise
            
    async def sync_playlist(self,
                          playlist_path: Path,
                          add_to_remote: Set[Path] = None,
                          add_to_local: Set[Path] = None,
                          remove_from_remote: Set[Path] = None,
                          remove_from_local: Set[Path] = None,
                          progress_callback: Optional[Callable[[float], None]] = None) -> None:
        """
        Sync playlist files between locations
        
        Args:
            playlist_path: Path to playlist file
            add_to_remote: Files to copy to remote
            add_to_local: Files to copy from remote
            remove_from_remote: Files to delete from remote
            remove_from_local: Files to delete locally
            progress_callback: Optional callback for progress updates
        """
        try:
            # Create backup before sync
            self.backup.create_backup(playlist_path)
            
            operations = []
            if add_to_remote:
                operations.append(self.add_to_remote(add_to_remote))
            if add_to_local:
                operations.append(self.add_to_local(add_to_local))
            if remove_from_remote:
                operations.append(self.remove_from_remote(remove_from_remote))
            if remove_from_local:
                operations.append(self.remove_from_local(remove_from_local))
                
            total_ops = len(operations)
            for i, operation in enumerate(operations):
                await operation(lambda p: progress_callback(
                    (i * 100 + p) / total_ops if progress_callback else None
                ))
                
        except Exception as e:
            logging.error(f"Error syncing playlist: {e}")
            raise