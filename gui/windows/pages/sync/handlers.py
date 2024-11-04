# gui/windows/pages/sync/handlers.py

"""Sync operation handlers."""
from pathlib import Path
from typing import Set, Optional, Dict
import asyncio
import logging
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, QThread
from functools import partial

from app.config import Config
from core.sync.ssh_handler import SSHHandler, SSHCredentials
from core.sync.file_comparator import FileComparator
from core.sync.sync_operations import SyncOperations
from core.sync.backup_manager import BackupManager
from data.cache.analysis_cache import AnalysisCache
from utils.logging.sync_logger import SyncLogger
from .state import SyncPageState, PlaylistAnalysis
from gui.dialogs.credentials_dialog import PasswordDialog

class AsyncHelper(QThread):
    """Helper class to run coroutines in Qt."""
    def __init__(self, coro, callback=None):
        super().__init__()
        self.coro = coro
        self.callback = callback

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.coro)
            if self.callback:
                self.callback(result)
        finally:
            loop.close()

class SyncOperationHandler(QObject):
    """Handles sync operations and coordinates with workers."""
    
    def __init__(self, state: SyncPageState):
        super().__init__()
        self.state = state
        self.logger = logging.getLogger('sync_handler')
        
        # Initialize paths
        self.local_base = Path(Config.LOCAL_BASE)
        self.playlists_dir = Path(Config.PLAYLISTS_DIR)
        self.backup_dir = Path(Config.BACKUP_DIR)
        
        # Initialize handlers
        self.ssh_handler = None
        self.file_comparator = None
        self.sync_ops = None
        self.backup_manager = BackupManager(self.backup_dir)
        self.sync_logger = SyncLogger(self.backup_dir / "logs")
        self.analysis_cache = AnalysisCache(Path.home() / ".m3u_library_manager" / "cache")
        
    def get_ssh_connection(self) -> bool:
        """Establish SSH connection if needed."""
        if self.ssh_handler is None:
            try:
                # Show password dialog if needed
                if not SSHCredentials._cached_password:
                    dialog = PasswordDialog()
                    result = dialog.get_credentials()
                    if not result.accepted:
                        self.state.report_error("SSH connection cancelled")
                        return False
                    password = result.password
                else:
                    password = SSHCredentials._cached_password
                    
                # Setup credentials
                credentials = SSHCredentials(
                    host=Config.SSH_HOST,
                    username=Config.SSH_USERNAME,
                    password=password,
                    remote_path=Config.SSH_REMOTE_PATH
                )
                
                self.ssh_handler = SSHHandler(credentials)
                
                # Test connection
                self.state.set_status("Testing SSH connection...")
                success, error = self.ssh_handler.test_connection()
                if not success:
                    self.state.report_error(f"SSH connection failed: {error}")
                    return False
                    
                # Setup comparator and sync ops
                self.file_comparator = FileComparator(self.ssh_handler)
                self.sync_ops = SyncOperations(
                    self.ssh_handler,
                    self.backup_manager,
                    self.local_base,
                    Config.SSH_REMOTE_PATH
                )
                
                return True
                
            except Exception as e:
                self.state.report_error(f"Failed to establish SSH connection: {e}")
                self.logger.error("SSH connection error", exc_info=True)
                return False
        return True
        
    def analyze_playlist(self, playlist_path: Path):
        """Start playlist analysis in a separate thread."""
        async def _analyze():
            if not self.get_ssh_connection():
                return
                
            try:
                self.state.is_analyzing = True
                self.state.analysis_started.emit(playlist_path)
                
                # Clear existing analysis
                self.analysis_cache.clear_result(playlist_path)
                
                # Run comparison
                result = await self.file_comparator.compare_locations(
                    playlist_path,
                    self.local_base,
                    Config.SSH_REMOTE_PATH,
                    self.state.update_progress
                )
                
                # Create analysis result
                analysis = PlaylistAnalysis(
                    missing_remotely=result.missing_remotely,
                    missing_locally=result.missing_locally,
                    is_synced=len(result.missing_remotely) == 0 and len(result.missing_locally) == 0,
                    exists_remotely=True
                )
                
                # Cache results
                self.analysis_cache.store_result(
                    playlist_path,
                    list(result.missing_remotely),
                    list(result.missing_locally)
                )
                
                # Log results
                self.sync_logger.log_comparison(
                    playlist_path,
                    result.missing_remotely,
                    result.missing_locally
                )
                
                # Update state
                self.state.set_analysis(playlist_path, analysis)
                
            except FileNotFoundError:
                # Handle missing playlist on remote
                analysis = PlaylistAnalysis(
                    missing_remotely=set(),
                    missing_locally=set(),
                    is_synced=False,
                    exists_remotely=False
                )
                self.state.set_analysis(playlist_path, analysis)
                self.state.report_error(f"Playlist not found on remote: {playlist_path.name}")
                
            except Exception as e:
                self.state.report_error(f"Analysis failed: {str(e)}")
                self.logger.error(f"Analysis error for {playlist_path}", exc_info=True)
                
            finally:
                self.state.is_analyzing = False

        helper = AsyncHelper(_analyze())
        helper.start()
            
    def analyze_all_playlists(self):
        """Start analysis of all playlists in a separate thread."""
        async def _analyze_all():
            if not self.get_ssh_connection():
                return
                
            try:
                self.state.is_analyzing = True
                self.state.analysis_all_started.emit()
                
                # Get all playlists except backup
                playlists = sorted(p for p in self.playlists_dir.glob("*.m3u")
                                 if p.name != "Love.bak.m3u")
                
                total_playlists = len(playlists)
                for i, playlist in enumerate(playlists, 1):
                    # Update progress
                    progress = int((i - 1) / total_playlists * 100)
                    self.state.update_progress(progress)
                    self.state.set_status(f"Analyzing {playlist.name}...")
                    
                    # Analyze playlist
                    await self._analyze_single(playlist)
                    
                self.state.update_progress(100)
                
            except Exception as e:
                self.state.report_error(f"Bulk analysis failed: {str(e)}")
                self.logger.error("Bulk analysis error", exc_info=True)
                
            finally:
                self.state.is_analyzing = False
                self.state.analysis_all_completed.emit()

        helper = AsyncHelper(_analyze_all())
        helper.start()

    async def _analyze_single(self, playlist_path: Path):
        """Internal method to analyze a single playlist."""
        try:
            # Run comparison
            result = await self.file_comparator.compare_locations(
                playlist_path,
                self.local_base,
                Config.SSH_REMOTE_PATH,
                None  # Skip progress updates for individual playlists in bulk analysis
            )
            
            # Create and store analysis
            analysis = PlaylistAnalysis(
                missing_remotely=result.missing_remotely,
                missing_locally=result.missing_locally,
                is_synced=len(result.missing_remotely) == 0 and len(result.missing_locally) == 0,
                exists_remotely=True
            )
            
            self.state.set_analysis(playlist_path, analysis)
            
        except Exception as e:
            self.logger.error(f"Error analyzing {playlist_path}: {e}")
            
    def sync_files(self, operation: str, files: Set[Path]):
        """Start sync operation in a separate thread."""
        async def _sync():
            if not files:
                return
                
            if not self.get_ssh_connection():
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
                await self.sync_ops.sync_playlist(
                    playlist_path=self.state.current_playlist,
                    progress_callback=self.state.update_progress,
                    **sync_params
                )
                
                # Clear cache and reanalyze
                self.analysis_cache.clear_result(self.state.current_playlist)
                await self._analyze_single(self.state.current_playlist)
                
                self.state.sync_completed.emit()
                
            except Exception as e:
                self.state.report_error(f"Sync failed: {str(e)}")
                self.logger.error("Sync error", exc_info=True)
                
            finally:
                self.state.is_syncing = False

        helper = AsyncHelper(_sync())
        helper.start()
            
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