# core/sync/backup_manager.py
from pathlib import Path
from datetime import datetime
import shutil
import logging

class BackupManager:
    """Manages playlist backups"""
    
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, playlist_path: Path) -> Path:
        """
        Create a backup of the playlist file
        
        Args:
            playlist_path: Path to playlist to backup
            
        Returns:
            Path to backup file
        """
        try:
            # Create timestamp-based backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{playlist_path.stem}_{timestamp}{playlist_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Copy playlist to backup location
            shutil.copy2(playlist_path, backup_path)
            
            # Clean old backups (keep last 5)
            self._cleanup_old_backups(playlist_path.stem)
            
            return backup_path
            
        except Exception as e:
            logging.error(f"Failed to create backup of {playlist_path}: {e}")
            raise
            
    def _cleanup_old_backups(self, playlist_stem: str, keep_count: int = 5):
        """
        Remove old backups, keeping only the specified number of most recent ones
        
        Args:
            playlist_stem: Base name of playlist without extension
            keep_count: Number of recent backups to keep
        """
        try:
            # Get all backups for this playlist
            backups = sorted(
                [f for f in self.backup_dir.glob(f"{playlist_stem}_*")],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups
            for backup in backups[keep_count:]:
                backup.unlink()
                
        except Exception as e:
            logging.error(f"Failed to cleanup old backups for {playlist_stem}: {e}")
            
    def restore_backup(self, backup_path: Path, playlist_path: Path) -> bool:
        """
        Restore a playlist from backup
        
        Args:
            backup_path: Path to backup file
            playlist_path: Path to restore to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not backup_path.exists():
                return False
                
            shutil.copy2(backup_path, playlist_path)
            return True
            
        except Exception as e:
            logging.error(f"Failed to restore backup {backup_path}: {e}")
            return False
            
    def list_backups(self, playlist_stem: str) -> list[Path]:
        """
        List available backups for a playlist
        
        Args:
            playlist_stem: Base name of playlist without extension
            
        Returns:
            List of backup file paths, sorted by date (newest first)
        """
        try:
            backups = sorted(
                [f for f in self.backup_dir.glob(f"{playlist_stem}_*")],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            return backups
            
        except Exception as e:
            logging.error(f"Failed to list backups for {playlist_stem}: {e}")
            return []