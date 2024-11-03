# utils/logging/sync_logger.py
from pathlib import Path
from datetime import datetime
import logging
from typing import Set, Optional

class SyncLogger:
    """Logs sync operations with detailed information"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('sync_operations')
        self.logger.setLevel(logging.INFO)
        
        # Create new log file for each session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"sync_{timestamp}.log"
        
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        
    def log_comparison(self,
                      playlist_path: Path,
                      missing_remotely: Set[Path],
                      missing_locally: Set[Path]):
        """Log results of location comparison"""
        self.logger.info(f"Comparing playlist: {playlist_path}")
        self.logger.info(f"Files missing remotely: {len(missing_remotely)}")
        self.logger.info(f"Files missing locally: {len(missing_locally)}")
        
        for path in missing_remotely:
            self.logger.debug(f"Missing remotely: {path}")
        for path in missing_locally:
            self.logger.debug(f"Missing locally: {path}")
            
    def log_sync_operation(self,
                          operation: str,
                          playlist_path: Path,
                          files: Set[Path],
                          success: bool,
                          error: Optional[str] = None):
        """Log sync operation details"""
        self.logger.info(f"Operation: {operation}")
        self.logger.info(f"Playlist: {playlist_path}")
        self.logger.info(f"Files affected: {len(files)}")
        self.logger.info(f"Status: {'Success' if success else 'Failed'}")
        
        if error:
            self.logger.error(f"Error details: {error}")
            
        for path in files:
            self.logger.debug(f"File: {path}")
            
    def log_backup(self,
                  playlist_path: Path,
                  backup_path: Path,
                  success: bool,
                  error: Optional[str] = None):
        """Log backup operation details"""
        self.logger.info(f"Backup operation for: {playlist_path}")
        self.logger.info(f"Backup saved to: {backup_path}")
        self.logger.info(f"Status: {'Success' if success else 'Failed'}")
        
        if error:
            self.logger.error(f"Error details: {error}")