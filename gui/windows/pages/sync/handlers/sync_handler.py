# gui/windows/pages/sync/handlers/sync_handler.py

from pathlib import Path
import logging
import asyncio
from typing import Set, Dict, Optional

from .async_base import AsyncOperation
from .connection_handler import ConnectionHandler
from ..state import PlaylistAnalysis
from core.playlist.safety import PlaylistSafety
from app.config import Config

class SyncHandler(AsyncOperation):
    """
    Handles sync operations with safety checks.
    Only modifies playlist (m3u) files, never touches the actual media files.
    """
    
    def __init__(self, state, connection: ConnectionHandler):
        super().__init__()
        self.state = state
        self.connection = connection
        self.safety = PlaylistSafety(Path(Config.BACKUP_DIR))
        self.logger = logging.getLogger('sync_handler')
        
    def sync_files(self, operation: str, files: Set[Path]):
        """Start a sync operation."""
        if not files:
            self.logger.warning("No files selected for sync operation")
            self.state.report_error("No files selected")
            return

        self.logger.info(f"Starting sync operation: {operation} with {len(files)} files")
        self.logger.debug(f"Current playlist: {self.state.current_playlist}")

        async def _sync():
            # Verify connection first
            self.logger.debug("Verifying SSH connection")
            success, error = self.connection.get_connection()
            if not success:
                self.logger.error(f"Connection failed: {error}")
                self.state.report_error(error)
                return
                
            try:
                # Create backup if operating on local playlist
                if self.state.current_playlist and (operation in ['add_local', 'delete_local']):
                    self.logger.debug("Creating backup before local operation")
                    backup_path = self.safety.create_backup(self.state.current_playlist)
                    if not backup_path:
                        self.logger.error("Failed to create backup")
                        raise RuntimeError("Failed to create backup")
                
                self.state.start_sync(operation)
                
                # Log sync parameters
                sync_params = {
                    'add_to_remote': files if operation == 'add_remote' else set(),
                    'add_to_local': files if operation == 'add_local' else set(),
                    'remove_from_remote': files if operation == 'delete_remote' else set(),
                    'remove_from_local': files if operation == 'delete_local' else set()
                }
                
                self.logger.debug(f"Sync parameters prepared:")
                for param, value in sync_params.items():
                    self.logger.debug(f"  {param}: {len(value)} files")
                
                if not self.state.current_playlist:
                    self.logger.error("No playlist selected for sync operation")
                    raise RuntimeError("No playlist selected")

                # Perform sync operation (only modifies m3u files)
                self.logger.info(f"Executing sync operation on playlist: {self.state.current_playlist}")
                success = await self.connection.sync_ops.sync_playlist(
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
            
    def upload_playlist(self, playlist_path: Path):
        """Upload a playlist file that doesn't exist on remote."""
        
        async def _upload():
            self.logger.debug(f"Starting playlist upload: {playlist_path.name}")
            
            try:
                from utils.m3u.parser import read_m3u, write_m3u, _normalize_path
                
                # Read and normalize paths
                paths = read_m3u(str(playlist_path))
                if not paths:
                    self.logger.error("Failed to read playlist content")
                    raise RuntimeError("Empty or invalid playlist")
                    
                # Normalize paths for remote
                normalized_paths = []
                for path in paths:
                    normalized = _normalize_path(path)
                    if not normalized:
                        continue
                    normalized_paths.append(normalized)
                    
                if not normalized_paths:
                    raise RuntimeError("No valid paths found in playlist")
                    
                # Calculate remote path
                remote_path = f"{self.connection.ssh_handler.credentials.remote_path}/{playlist_path.name}"
                
                # Create temporary file with normalized paths
                import tempfile
                temp_path = Path(tempfile.gettempdir()) / f"upload_{playlist_path.name}"
                
                try:
                    # Write normalized paths to temp file
                    write_m3u(str(temp_path), normalized_paths, use_absolute_paths=False)
                    
                    # Upload to remote
                    if not self.connection.ssh_handler.copy_to_remote(temp_path, remote_path):
                        raise RuntimeError("Failed to upload playlist to remote")
                        
                finally:
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
                        
                # Reanalyze after upload
                analysis = await self._analyze_after_sync(playlist_path)
                if analysis:
                    self.state.set_analysis(playlist_path, analysis)
                    
                return True
                
            except Exception as e:
                self.logger.error(f"Upload failed: {e}", exc_info=True)
                raise RuntimeError(f"Upload failed: {str(e)}")
                    
            finally:
                self.state.finish_sync()
                    
        self._start_operation(_upload())
        
    async def _analyze_after_sync(self, playlist_path: Path):
        """Reanalyze playlist after sync operation."""
        try:
            self.logger.debug(f"Starting post-sync analysis for {playlist_path}")
            result = await self.connection.file_comparator.compare_locations(
                playlist_path,
                self.connection.local_base,
                Config.SSH_REMOTE_PATH,
                None  # Skip progress updates for quick reanalysis
            )
            
            from ..state import PlaylistAnalysis
            return PlaylistAnalysis(
                missing_remotely=result.missing_remotely,
                missing_locally=result.missing_locally,
                exists_remotely=result.exists_remotely
            )
            
        except Exception as e:
            self.logger.error(f"Reanalysis failed: {e}")
            return None

    def stop(self):
        """Stop current operation."""
        self.logger.debug("Stopping sync operation")
        if self.current_worker:
            self.current_worker.stop()
            
    def cleanup(self):
        """Clean up resources."""
        self.logger.debug("Cleaning up sync handler")
        self.stop()
        super().cleanup()