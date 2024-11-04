# gui/windows/pages/sync/handlers/sync_handler.py

from pathlib import Path
from typing import Set
from PyQt6.QtWidgets import QMessageBox

from app.config import Config
from .async_base import AsyncOperation
from .connection_handler import ConnectionHandler
from ..state import SyncPageState

class SyncHandler(AsyncOperation):
    """Handles sync operations."""
    
    def __init__(self, state: SyncPageState, connection: ConnectionHandler):
        super().__init__()
        self.state = state
        self.connection = connection
        
    def sync_files(self, operation: str, files: Set[Path]):
        """Start a sync operation."""
        if not files:
            return
            
        async def _sync():
            success, error = self.connection.get_connection()
            if not success:
                self.state.report_error(error)
                return
                
            try:
                # Confirm deletions
                if operation.startswith('delete'):
                    location = 'local' if operation == 'delete_local' else 'remote'
                    if not self._confirm_deletion(location, len(files)):
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
                self.state.report_error(f"Sync failed: {str(e)}")
                self.logger.error("Sync error", exc_info=True)
                
            finally:
                self.state.is_syncing = False
                
        self._start_operation(
            _sync(),
            progress_callback=self.state.update_progress
        )
            
    def _confirm_deletion(self, location: str, count: int) -> bool:
        """Show confirmation dialog for deletions."""
        response = QMessageBox.question(
            None,
            "Confirm Deletion",
            f"Are you sure you want to delete {count} files from the {location} location?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes