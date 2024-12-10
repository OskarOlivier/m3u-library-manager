# gui/windows/pages/sync/handlers/sync_handler.py

from pathlib import Path
import logging
import asyncio
from typing import Optional, Set, Dict, Any
from PyQt6.QtCore import Qt

from gui.workers.async_base import AsyncOperation
from core.context import SyncService, PlaylistService
from ..state import PlaylistAnalysis

class SyncHandler(AsyncOperation):
    """Handles sync operations with proper safety checks."""
    
    def __init__(self, state, connection_handler, sync_service: SyncService, playlist_service: PlaylistService, ui_service):
        super().__init__()
        self.state = state
        self.connection = connection_handler
        self.sync_service = sync_service
        self.playlist_service = playlist_service
        self.ui_service = ui_service
        self.logger = logging.getLogger('sync_handler')

    def upload_playlist(self, playlist_path: Path):
        """Upload a playlist file that doesn't exist on remote."""
        
        # Verify connection before proceeding
        if not self._check_connection():
            return

        async def _upload():
            self.logger.debug(f"Starting playlist upload: {playlist_path.name}")
            
            try:
                # Get confirmation first
                if not self.ui_service.confirm_operation(
                    "Confirm Upload",
                    f"Upload playlist {playlist_path.name} to remote location?"
                ):
                    return False

                self.state.start_sync("upload")

                # Create backup first
                backup_path = self.playlist_service.backup_manager.create_backup(playlist_path)
                if not backup_path:
                    raise RuntimeError("Failed to create backup")
                
                # Show backup notification
                await asyncio.to_thread(
                    self.ui_service.show_backup_created,
                    backup_path
                )

                # Perform upload
                result = await self.sync_service.sync_ops.upload_playlist(
                    playlist_path,
                    progress_callback=lambda p: self.state.update_progress(p)
                )
                
                if not result:
                    raise RuntimeError("Upload operation failed")

                # Re-analyze after upload
                analysis = await self._analyze_after_sync(playlist_path)
                if analysis:
                    self.state.set_analysis(playlist_path, analysis)
                    
                self.state.set_status(f"Successfully uploaded {playlist_path.name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Upload failed: {e}", exc_info=True)
                self.state.report_error(f"Upload failed: {str(e)}")
                return False
                    
            finally:
                self.state.finish_sync()
                    
        self._start_operation(_upload())

    def _check_connection(self) -> bool:
        """Check SSH connection before starting operation."""
        success, error = self.connection.get_connection()
        if not success:
            self.state.report_error(error)
            return False
        return True
        
    def sync_files(self, operation: str, files: Set[Path]):
        """Start a sync operation."""
        if not files:
            self.logger.warning("No files selected for sync operation")
            self.state.report_error("No files selected")
            return

        self.logger.info(f"Starting sync operation: {operation} with {len(files)} files")
        self.logger.debug(f"Current playlist: {self.state.current_playlist}")

        # Verify connection before proceeding
        if not self._check_connection():
            return

        # Get user confirmation
        if not SafetyDialogs.confirm_sync_operation(operation, len(files)):
            return

        async def _sync():
            try:
                # Create backup if operating on local playlist
                if self.state.current_playlist and (operation in ['add_to_local_playlist', 'remove_from_local_playlist']):
                    self.logger.debug("Creating backup before local operation")
                    backup_path = self.playlist_service.backup_manager.create_backup(
                        self.state.current_playlist
                    )
                    if not backup_path:
                        raise RuntimeError("Failed to create backup")
                    
                    # Show backup notification
                    SafetyDialogs.show_backup_created(backup_path)

                self.state.start_sync(operation)
                
                # Log sync parameters
                sync_params = {
                    'add_to_remote': files if operation == 'add_to_remote_playlist' else set(),
                    'add_to_local': files if operation == 'add_to_local_playlist' else set(),
                    'remove_from_remote': files if operation == 'remove_from_remote_playlist' else set(),
                    'remove_from_local': files if operation == 'remove_from_local_playlist' else set()
                }
                
                self.logger.debug(f"Sync parameters prepared:")
                for param, value in sync_params.items():
                    self.logger.debug(f"  {param}: {len(value)} files")
                
                if not self.state.current_playlist:
                    self.logger.error("No playlist selected for sync operation")
                    raise RuntimeError("No playlist selected")

                # Perform sync operation (only modifies m3u files)
                self.logger.info(f"Executing sync operation on playlist: {self.state.current_playlist}")
                success = await self.sync_service.sync_ops.sync_playlist(
                    playlist_path=self.state.current_playlist,
                    progress_callback=self.state.update_progress,
                    **sync_params
                )

                if not success:
                    self.logger.error("Sync operation failed")
                    self.state.report_error(f"Sync operation failed")
                    return

                # Reanalyze playlist after successful sync
                self.logger.debug("Starting post-sync analysis")
                analysis = await self._analyze_after_sync(self.state.current_playlist)
                if analysis:
                    self.logger.debug("Updating analysis results")
                    self.state.set_analysis(self.state.current_playlist, analysis)

                self.logger.info("Sync completed successfully")
                self.state.set_status("Sync completed successfully")
                    
            except Exception as e:
                self.logger.error(f"Sync failed: {e}", exc_info=True)
                self.state.report_error(f"Sync failed: {str(e)}")
                
            finally:
                self.state.finish_sync()
                
        self._start_operation(_sync())
                    
    async def _analyze_after_sync(self, playlist_path: Path) -> Optional[PlaylistAnalysis]:
        """Re-analyze playlist after sync operation."""
        try:
            self.logger.debug(f"Starting post-sync analysis for {playlist_path}")
            result = await self.connection.file_comparator.compare_locations(
                playlist_path,
                self.connection.local_base,
                self.sync_service.ssh_handler.credentials.remote_path,
                None  # Skip progress updates for quick reanalysis
            )
            
            return PlaylistAnalysis(
                missing_remotely=result.missing_remotely,
                missing_locally=result.missing_locally,
                exists_remotely=result.exists_remotely
            )
            
        except Exception as e:
            self.logger.error(f"Re-analysis failed: {e}")
            return None


    def cleanup(self):
        """Clean up resources."""
        super().cleanup()