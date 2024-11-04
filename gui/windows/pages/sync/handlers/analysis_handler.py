# gui/windows/pages/sync/handlers/analysis_handler.py

from pathlib import Path
import logging
import asyncio
from typing import Optional, List

from app.config import Config
from data.cache.analysis_cache import AnalysisCache
from utils.logging.sync_logger import SyncLogger
from ..state import SyncPageState, PlaylistAnalysis
from .async_base import AsyncOperation
from .connection_handler import ConnectionHandler

class AnalysisHandler(AsyncOperation):
    """Handles playlist analysis operations."""
    
    def __init__(self, state: SyncPageState, connection: ConnectionHandler):
        super().__init__()
        self.state = state
        self.connection = connection
        
        # Set up logging
        self.logger = logging.getLogger('AnalysisHandler')
        self.logger.setLevel(logging.DEBUG)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Initialize support components
        self.cache = AnalysisCache(Path.home() / ".m3u_library_manager" / "cache")
        self.sync_logger = SyncLogger(Path(Config.BACKUP_DIR) / "logs")

    def _check_connection(self) -> bool:
        """Check SSH connection before starting analysis."""
        self.logger.debug("Checking SSH connection")
        success, error = self.connection.get_connection()
        if not success:
            self.logger.error(f"Connection failed: {error}")
            self.state.report_error(error)
            return False
        return True
            
    async def _analyze_playlist(self, playlist_path: Path) -> Optional[PlaylistAnalysis]:
        """Internal method to analyze a single playlist."""
        self.logger.debug(f"Starting analysis of playlist: {playlist_path.name}")
        
        if not self.current_worker or not self.current_worker._is_running:
            self.logger.debug("Worker not running, abandoning analysis")
            return None
            
        try:
            self.logger.debug(f"Clearing existing analysis for {playlist_path.name}")
            self.cache.clear_result(playlist_path)
            
            self.logger.debug(f"Running comparison for {playlist_path.name}")
            result = await self.connection.file_comparator.compare_locations(
                playlist_path,
                self.connection.local_base,
                Config.SSH_REMOTE_PATH,
                self.state.update_progress
            )
            
            self.logger.debug("Allowing event processing")
            await asyncio.sleep(0)
            
            if not self.current_worker or not self.current_worker._is_running:
                self.logger.debug("Worker stopped during analysis")
                return None
            
            self.logger.debug("Creating analysis result")
            analysis = PlaylistAnalysis(
                missing_remotely=result.missing_remotely,
                missing_locally=result.missing_locally,
                is_synced=len(result.missing_remotely) == 0 and len(result.missing_locally) == 0,
                exists_remotely=True
            )
            
            self.logger.debug("Caching results")
            self.cache.store_result(
                playlist_path,
                list(result.missing_remotely),
                list(result.missing_locally)
            )
            
            self.logger.debug("Logging comparison results")
            self.sync_logger.log_comparison(
                playlist_path,
                result.missing_remotely,
                result.missing_locally
            )
            
            self.logger.debug(f"Analysis complete for {playlist_path.name}")
            return analysis
            
        except FileNotFoundError:
            self.logger.warning(f"Playlist not found: {playlist_path.name}")
            return PlaylistAnalysis(
                missing_remotely=set(),
                missing_locally=set(),
                is_synced=False,
                exists_remotely=False
            )
        except Exception as e:
            self.logger.error(f"Error analyzing {playlist_path.name}: {e}", exc_info=True)
            raise
            
    def analyze_playlist(self, playlist_path: Path):
        """Start analysis of a single playlist."""
        self.logger.info(f"Starting single playlist analysis: {playlist_path.name}")

        # Check connection before starting
        if not self._check_connection():
            return
        
        async def _analyze():
            self.state.is_analyzing = True
            self.state.analysis_started.emit(playlist_path)
            
            try:
                analysis = await self._analyze_playlist(playlist_path)
                if analysis:
                    self.logger.debug("Setting analysis result")
                    self.state.set_analysis(playlist_path, analysis)
                    
                    if not analysis.exists_remotely:
                        self.logger.warning(f"Playlist not found on remote: {playlist_path.name}")
                        self.state.report_error(f"Playlist not found on remote: {playlist_path.name}")
                        
            except Exception as e:
                self.logger.error(f"Analysis failed: {str(e)}")
                self.state.report_error(f"Analysis failed: {str(e)}")
                
            finally:
                self.state.is_analyzing = False
                
        self._start_operation(
            _analyze(),
            progress_callback=self.state.update_progress
        )
        
    def analyze_all_playlists(self, playlists_dir: Path):
        """Start analysis of all playlists."""
        self.logger.info("Starting bulk playlist analysis")
        
        # Check connection before starting
        if not self._check_connection():
            return
        
        async def _analyze_all():
            self.state.is_analyzing = True
            self.state.analysis_all_started.emit()
            
            try:
                self.logger.debug("Getting playlist list")
                playlists = sorted(p for p in playlists_dir.glob("*.m3u")
                                 if p.name != "Love.bak.m3u")
                
                self.logger.info(f"Found {len(playlists)} playlists to analyze")
                total = len(playlists)
                failed_playlists = []
                
                for i, playlist in enumerate(playlists, 1):
                    if not self.current_worker or not self.current_worker._is_running:
                        self.logger.debug("Bulk analysis cancelled")
                        break
                        
                    progress = int((i - 1) / total * 100)
                    self.state.update_progress(progress)
                    self.state.set_status(f"Analyzing {playlist.name}...")
                    
                    try:
                        self.logger.info(f"Analyzing playlist {i}/{total}: {playlist.name}")
                        analysis = await self._analyze_playlist(playlist)
                        
                        if analysis:
                            self.logger.debug(f"Setting analysis for {playlist.name}")
                            self.state.set_analysis(playlist, analysis)
                            
                            if not analysis.exists_remotely:
                                failed_playlists.append(playlist.name)
                                
                    except Exception as e:
                        self.logger.error(f"Error analyzing {playlist.name}: {e}")
                        failed_playlists.append(playlist.name)
                        continue  # Continue with next playlist
                    
                    self.logger.debug("Processing events")
                    await asyncio.sleep(0)
                    
                if self.current_worker and self.current_worker._is_running:
                    self.logger.info("Bulk analysis completed")
                    self.state.update_progress(100)
                    
                    if failed_playlists:
                        failed_msg = f"Failed to analyze {len(failed_playlists)} playlists: {', '.join(failed_playlists)}"
                        self.logger.warning(failed_msg)
                        self.state.report_error(failed_msg)
                    
            except Exception as e:
                self.logger.error(f"Bulk analysis failed: {str(e)}", exc_info=True)
                self.state.report_error(f"Bulk analysis failed: {str(e)}")
                
            finally:
                self.state.is_analyzing = False
                self.state.analysis_all_completed.emit()
                self.logger.info("Bulk analysis operation finished")
                
        self._start_operation(
            _analyze_all(),
            progress_callback=self.state.update_progress
        )