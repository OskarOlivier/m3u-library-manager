# gui/windows/pages/sync/handlers/sync_handler.py

from pathlib import Path
from typing import Set
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
                if not self._confirm_operation(operation, files):
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
                self.state.set_status(f"Starting {operation} operation...")
                
                # Perform the sync operation
                await self._execute_sync_operation(operation, files)
                
                # Trigger reanalysis of the playlist
                if self.state.current_playlist:
                    self.state.set_status("Updating analysis...")
                    analysis = await self._analyze_after_sync(self.state.current_playlist)
                    if analysis:
                        self.state.set_analysis(self.state.current_playlist, analysis)
                
                self.state.sync_completed.emit()
                self.state.set_status(f"{operation} completed successfully")
                
            except Exception as e:
                self.logger.error(f"Sync failed: {e}", exc_info=True)
                self.state.report_error(f"Sync failed: {str(e)}")
                
            finally:
                self.state.is_syncing = False
                
    def _confirm_operation(self, operation: str, files: Set[Path]) -> bool:
        """Get user confirmation for operation."""
        if operation.startswith('delete'):
            location = 'local' if operation == 'delete_local' else 'remote'
            return SafetyDialogs.confirm_delete_files(location, len(files))
        else:
            operation_name = operation.replace('_', ' ').title()
            return SafetyDialogs.confirm_sync_operation(operation_name, len(files))
            
    async def _execute_sync_operation(self, operation: str, files: Set[Path]):
        """Execute the actual sync operation."""
        if not self.connection.sync_ops:
            raise RuntimeError("Sync operations handler not initialized")
            
        total_files = len(files)
        processed_files = 0
        
        for file in files:
            if not self.current_worker or not self.current_worker._is_running:
                self.logger.debug("Operation cancelled")
                break
                
            try:
                # Update progress for each file
                progress = int((processed_files / total_files) * 100)
                self.state.update_progress(progress)
                self.state.set_status(f"Processing: {file.name}")
                
                # Perform operation
                if operation == 'add_remote':
                    await self.connection.sync_ops.add_to_remote({file})
                elif operation == 'add_local':
                    await self.connection.sync_ops.add_to_local({file})
                elif operation == 'delete_remote':
                    await self.connection.sync_ops.remove_from_remote({file})
                elif operation == 'delete_local':
                    await self.connection.sync_ops.remove_from_local({file})
                    
                processed_files += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {file}: {e}")
                self.state.report_error(f"Error processing {file.name}")
                
        # Final progress update
        self.state.update_progress(100)
            
    async def _analyze_after_sync(self, playlist_path: Path):
        """Reanalyze playlist after sync operation."""
        try:
            result = await self.connection.file_comparator.compare_locations(
                playlist_path,
                self.connection.local_base,
                Config.SSH_REMOTE_PATH,
                None  # Skip progress updates for quick reanalysis
            )
            
            return PlaylistAnalysis(
                missing_remotely=result.missing_remotely,
                missing_locally=result.missing_locally,
                exists_remotely=result.exists_remotely
            )
            
        except Exception as e:
            self.logger.error(f"Reanalysis failed: {e}")
            return None
            
    def upload_playlist(self, playlist_path: Path):
        """Upload a playlist that doesn't exist on remote."""
        async def _upload():
            # Check connection
            self.logger.debug("Starting playlist upload operation")
            success, error = self.connection.get_connection()
            if not success:
                self.logger.error(f"Connection failed: {error}")
                self.state.report_error(error)
                return
                
            try:
                # Confirm operation
                if not SafetyDialogs.confirm_sync_operation("Upload Playlist", 1):
                    self.logger.debug("Upload cancelled by user")
                    return
                    
                self.state.is_syncing = True
                self.state.sync_started.emit("upload_playlist")
                self.state.set_status(f"Uploading playlist: {playlist_path.name}")
                
                # Calculate remote path
                remote_path = f"{Config.SSH_REMOTE_PATH}/{playlist_path.name}"
                self.logger.debug(f"Remote path: {remote_path}")
                
                # Verify local playlist
                if not playlist_path.exists():
                    self.logger.error("Local playlist file not found")
                    self.state.report_error("Local playlist file not found")
                    return
                    
                self.logger.debug("Starting file transfer...")
                # Perform the upload
                if not self.connection.ssh_handler.copy_to_remote(playlist_path, remote_path):
                    self.logger.error("Upload failed in ssh_handler.copy_to_remote")
                    self.state.report_error("Failed to upload playlist")
                    return
                    
                self.logger.debug("File transfer completed, starting reanalysis")
                
                # Reanalyze after upload
                self.state.set_status("Updating analysis...")
                analysis = await self._analyze_after_sync(playlist_path)
                if analysis:
                    self.state.set_analysis(playlist_path, analysis)
                    
                self.state.sync_completed.emit()
                self.state.set_status("Upload completed successfully")
                self.logger.debug("Upload operation completed successfully")
                    
            except Exception as e:
                self.logger.error(f"Upload failed: {e}", exc_info=True)
                self.state.report_error(f"Upload failed: {str(e)}")
                    
            finally:
                self.state.is_syncing = False
                self.logger.debug("Upload operation finished")
                    
        self._start_operation(
            _upload(),
            progress_callback=self.state.update_progress
        )
        
    def cleanup(self):
        """Clean up resources."""
        super().cleanup()