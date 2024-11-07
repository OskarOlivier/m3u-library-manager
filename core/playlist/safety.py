# core/playlist/safety.py

from pathlib import Path
from typing import Optional, List
from datetime import datetime
import shutil
import hashlib
import logging

class PlaylistSafety:
    """Handles safety checks and backups for playlist operations"""
    
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('playlist_safety')
        
    def create_backup(self, playlist_path: Path) -> Optional[Path]:
        """
        Create a backup of a playlist before modification.
        
        Args:
            playlist_path: Path to playlist to backup
            
        Returns:
            Path to backup file if successful, None if failed
        """
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{playlist_path.stem}_{timestamp}{playlist_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Create backup
            shutil.copy2(playlist_path, backup_path)
            
            # Verify backup
            if not self._verify_backup(playlist_path, backup_path):
                self.logger.error(f"Backup verification failed for {playlist_path}")
                backup_path.unlink(missing_ok=True)
                return None
                
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
            
    def _verify_backup(self, source: Path, backup: Path) -> bool:
        """Verify backup matches source file"""
        try:
            source_hash = self._get_file_hash(source)
            backup_hash = self._get_file_hash(backup)
            return source_hash == backup_hash
        except Exception as e:
            self.logger.error(f"Backup verification error: {e}")
            return False
            
    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA-256 hash of file contents"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore a playlist from backup.
        
        Args:
            backup_path: Path to backup file
            target_path: Path to restore to
            
        Returns:
            True if successful
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
                
            # Create backup of current state just in case
            current_backup = self.create_backup(target_path)
            
            # Restore from backup
            shutil.copy2(backup_path, target_path)
            
            # Verify restoration
            if not self._verify_backup(backup_path, target_path):
                self.logger.error("Restoration verification failed")
                if current_backup:
                    shutil.copy2(current_backup, target_path)
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
            
    def list_backups(self, playlist_stem: str) -> List[Path]:
        """Get list of available backups for a playlist"""
        try:
            backups = sorted(
                [f for f in self.backup_dir.glob(f"{playlist_stem}_*")],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            return backups
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []
            
    def cleanup_old_backups(self, playlist_stem: str, keep_count: int = 5):
        """Remove old backups, keeping only the most recent ones"""
        try:
            backups = self.list_backups(playlist_stem)
            for backup in backups[keep_count:]:
                backup.unlink()
        except Exception as e:
            self.logger.error(f"Failed to cleanup backups: {e}")