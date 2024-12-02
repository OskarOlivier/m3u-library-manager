# gui/windows/pages/maintenance/handlers/repair_handler.py

from pathlib import Path
import logging
import asyncio
from typing import Dict, Set, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from core.playlist.safety import PlaylistSafety
from app.config import Config
from utils.m3u.parser import read_m3u, write_m3u
from gui.dialogs.safety_dialogs import SafetyDialogs
from gui.workers.async_base import AsyncOperation

class RepairHandler(AsyncOperation):
    """
    Handles playlist repair operations with proper safety checks.
    Includes file relocation and reference updating.
    """
    
    # Signals
    operation_started = pyqtSignal(str)  # Operation description
    operation_completed = pyqtSignal(bool)  # Success status
    progress_updated = pyqtSignal(int)  # Progress value
    status_updated = pyqtSignal(str)  # Status message
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('repair_handler')
        self.safety = PlaylistSafety(Path(Config.BACKUP_DIR))
        
    def repair_playlist(self, playlist_path: Path, repairs: Dict[Path, Path]):
        """
        Start playlist repair operation.
        
        Args:
            playlist_path: Path to playlist to repair
            repairs: Dictionary mapping original paths to their replacements
        """
        if not repairs:
            self.logger.warning("No repairs specified")
            return
            
        async def _repair():
            try:
                # Get confirmation
                if not SafetyDialogs.confirm_repair(playlist_path.name):
                    self.logger.info("Repair cancelled by user")
                    return
                    
                # Start operation
                self.operation_started.emit("Repair Playlist")
                self.status_updated.emit(f"Creating backup of {playlist_path.name}...")
                self.progress_updated.emit(10)
                
                # Create backup
                backup_path = self.safety.create_backup(playlist_path)
                if not backup_path:
                    self.error_occurred.emit("Failed to create backup")
                    self.operation_completed.emit(False)
                    return
                    
                # Show backup notification
                SafetyDialogs.show_backup_created(backup_path)
                self.progress_updated.emit(25)
                
                # Read playlist content
                self.status_updated.emit("Reading playlist content...")
                paths = read_m3u(str(playlist_path))
                if paths is None:
                    self.error_occurred.emit("Failed to read playlist")
                    self.operation_completed.emit(False)
                    return
                    
                # Update paths
                self.status_updated.emit("Updating file references...")
                modified = False
                new_paths = []
                
                total_paths = len(paths)
                for i, path in enumerate(paths, 1):
                    # Update progress
                    progress = 25 + int((i / total_paths) * 50)
                    self.progress_updated.emit(progress)
                    
                    path_obj = Path(path)
                    if path_obj in repairs:
                        new_paths.append(str(repairs[path_obj]))
                        modified = True
                    else:
                        new_paths.append(path)
                        
                    # Allow other events
                    await asyncio.sleep(0)
                    
                if not modified:
                    self.status_updated.emit("No changes needed")
                    self.operation_completed.emit(True)
                    return
                    
                # Write updated content
                self.status_updated.emit("Writing updates...")
                self.progress_updated.emit(75)
                
                write_m3u(str(playlist_path), new_paths)
                
                # Verify write
                verification_paths = read_m3u(str(playlist_path))
                if verification_paths != new_paths:
                    self.error_occurred.emit("Failed to verify changes")
                    self._restore_backup(backup_path, playlist_path)
                    self.operation_completed.emit(False)
                    return
                    
                # Success
                self.progress_updated.emit(100)
                self.status_updated.emit("Playlist repaired successfully")
                self.operation_completed.emit(True)
                
            except Exception as e:
                self.logger.error(f"Repair failed: {e}", exc_info=True)
                self.error_occurred.emit(f"Repair failed: {str(e)}")
                self.operation_completed.emit(False)
                
        self._start_operation(
            _repair(),
            progress_callback=lambda p: self.progress_updated.emit(p)
        )
                
    def _restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore from backup after failed operation."""
        try:
            self.status_updated.emit("Restoring from backup...")
            return self.safety.restore_backup(backup_path, target_path)
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
            
    def cleanup(self):
        """Clean up resources."""
        super().cleanup()