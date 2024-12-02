# gui/windows/pages/sync/handlers/analysis_handler.py

from pathlib import Path
import logging
import asyncio
from typing import Optional, List

from app.config import Config
from data.cache.analysis_cache import AnalysisCache
from utils.logging.sync_logger import SyncLogger
from gui.workers.async_base import AsyncOperation
from core.context import SyncService
from ..state import PlaylistAnalysis

class AnalysisHandler(AsyncOperation):
    """Handles playlist analysis operations."""
    
    def __init__(self, state, connection_handler, sync_service: SyncService):
        super().__init__()
        self.state = state
        self.connection = connection_handler
        self.sync_service = sync_service
        self.logger = logging.getLogger('analysis_handler')
        
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
                exists_remotely=result.exists_remotely
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
        """Start analysis of all playlists in directory."""
        self.logger.info("Starting bulk playlist analysis")

        # Check connection before starting
        if not self._check_connection():
            return

        async def _analyze_all():
            try:
                # Get regular playlists (excluding backups and unplaylisted)
                from utils.playlist import get_regular_playlists
                playlists = get_regular_playlists(playlists_dir)
                total_playlists = len(playlists)

                if not playlists:
                    self.state.report_error("No playlists found")
                    return

                # Start bulk analysis
                self.state.is_analyzing = True
                self.state.analysis_all_started.emit()
                self.state.start_bulk_analysis(total_playlists)

                for i, playlist in enumerate(playlists, 1):
                    if not self.current_worker or not self.current_worker._is_running:
                        self.logger.debug("Analysis cancelled")
                        break

                    try:
                        # Update progress
                        progress = int((i - 1) / total_playlists * 100)
                        self.state.update_progress(progress)
                        self.state.set_status(f"Analyzing {playlist.name}...")

                        # Analyze playlist
                        analysis = await self._analyze_playlist(playlist)
                        if analysis:
                            self.state.set_analysis(playlist, analysis)

                        # Update progress again after completion
                        self.state.update_analysis_progress(playlist)

                    except Exception as e:
                        self.logger.error(f"Error analyzing {playlist.name}: {e}")
                        continue

                # Final progress update
                self.state.update_progress(100)
                self.state.set_status("Analysis complete")

            except Exception as e:
                self.logger.error(f"Bulk analysis failed: {e}")
                self.state.report_error(f"Bulk analysis failed: {str(e)}")

            finally:
                self.state.is_analyzing = False
                self.state.finish_analysis()

        self._start_operation(
            _analyze_all(),
            progress_callback=self.state.update_progress
        )

    def cleanup(self):
        """Clean up resources."""
        super().cleanup()