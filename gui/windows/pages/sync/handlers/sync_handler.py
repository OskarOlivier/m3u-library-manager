# gui/windows/pages/sync/handlers/sync_handler.py

from pathlib import Path
from typing import Set
from PyQt6.QtWidgets import QMessageBox
import logging

from .async_base import AsyncOperation
from .connection_handler import ConnectionHandler
from ..state import SyncPageState
from ..components.safety_dialogs import SafetyDialogs
from core.playlist.safety import PlaylistSafety
from app.config import Config

class SyncHandler(AsyncOperation):
    """Handles sync operations with safety checks."""
    
    def __init__(self, state: SyncPageState, connection: ConnectionHandler):
        super().__init__()
        self.state = state
        self.connection = connection
        self.safety = PlaylistSafety(Path(Config.BACKUP_DIR))
        self.logger = logging.getLogger('sync_handler')
        
    def sync_files(self, operation: str, files: Set[Path]):
        """Start a sync operation with safety checks."""
        if not files:
            return
            
        async def _sync():
            # Check connection
            success, error = self.connection.get_connection()
            if not success:
                self.state.report_error(error)
                return
                
            try:
                # Get confirmation based on operation type
                if operation.startswith('delete'):
                    location = 'local' if operation == 'delete_local' else 'remote'
                    if not SafetyDialogs.confirm_delete_files(location, len(files)):
                        return
                else:
                    operation_name = operation.replace('_', ' ').title()
                    if not SafetyDialogs.confirm_sync_operation(operation_name, len(files)):
                        return
                        
                # Create backup for affected playlist
                if self.state.current_playlist:
                    self.logger.info("Creating backup...")
                    backup_path = self.safety.create_backup(self.state.current_playlist)
                    if backup_path:
                        self.logger.info(f"Backup created at {backup_path}")
                        SafetyDialogs.show_backup_created(backup_path)
                    else:
                        error_msg = "Failed to create backup"
                        self.logger.error(error_msg)
                        self.state.report_error(error_msg)
                        return
                
                self.state.is_syncing = True
                self.state.sync_started.emit(operation)
                
                # Prepare sync parameters
                sync_params = {
                    'add_to_remote': files if operation == 'add_remote' else set(),
                    'add_to_local': files if operation == 'add_local' else set(),
                    'remove_from_remote': files if operation == 'delete_remote' else set(),
                    'remove_from_local': files if operation == 'delete_local' else set()
                }
                
                # Perform sync
                await self.connection.sync_ops.sync_playlist(
                    playlist_path=self.state.current_playlist,
                    progress_callback=self.state.update_progress,
                    **sync_params
                )
                
                self.state.sync_completed.emit()
                
            except Exception as e:
                self.logger.error(f"Sync failed: {e}", exc_info=True)
                self.state.report_error(f"Sync failed: {str(e)}")
                
            finally:
                self.state.is_syncing = False
                
        self._start_operation(
            _sync(),
            progress_callback=self.state.update_progress
        )

    def cleanup(self):
        """Clean up resources."""
        super().cleanup()