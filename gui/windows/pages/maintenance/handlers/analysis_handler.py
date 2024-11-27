# gui/windows/pages/maintenance/handlers/analysis_handler.py

from pathlib import Path
import logging
import asyncio
from typing import Optional, List
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

from app.config import Config
from utils.m3u.parser import read_m3u
from gui.workers.async_base import AsyncOperation
from ..state import PlaylistAnalysis

class AnalysisHandler(AsyncOperation):
    """Handles playlist analysis operations."""
    
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.logger = logging.getLogger('analysis_handler')

    async def _analyze_playlist(self, playlist_path: Path) -> Optional[PlaylistAnalysis]:
        """Internal method to analyze a single playlist."""
        try:
            self.state.set_status(f"Reading playlist: {playlist_path.name}")
            paths = read_m3u(str(playlist_path))
            if paths is None:
                self.state.report_error(f"Failed to read playlist: {playlist_path.name}")
                return None
                
            self.state.set_status(f"Checking files in {playlist_path.name}")
            # Find missing files
            missing_files = set()
            valid_files = []
            total_files = len(paths)
            
            for i, path in enumerate(paths):
                file_path = Path(path)
                if not file_path.exists():
                    missing_files.add(file_path)
                else:
                    valid_files.append(file_path)
                    
                if i % 10 == 0:  # Update progress every 10 files
                    self.state.update_progress(int((i / total_files) * 50))  # First 50% for file checking
                    
            self.state.set_status(f"Analyzing sort order of {playlist_path.name}")
            # Detect sort method
            sort_method = await self._detect_sort_method(valid_files)
            
            analysis = PlaylistAnalysis(
                missing_files=missing_files,
                sort_method=sort_method,
                has_duplicates=len(paths) != len(set(paths)),
                total_files=len(paths),
                valid_files=len(valid_files),
                exists_remotely=True
            )
            
            # Log the results
            self.logger.info(f"Analysis complete for {playlist_path.name}:")
            self.logger.info(f"- Missing files: {len(missing_files)}")
            self.logger.info(f"- Valid files: {len(valid_files)}")
            self.logger.info(f"- Sort method: {sort_method or 'custom'}")
            self.logger.info(f"- Has duplicates: {analysis.has_duplicates}")
            
            # Update final status
            status_parts = []
            if missing_files:
                status_parts.append(f"{len(missing_files)} missing files")
            if analysis.has_duplicates:
                status_parts.append("has duplicates")
            if sort_method:
                status_parts.append(f"sorted by {sort_method}")
            
            status = f"Analysis complete: {', '.join(status_parts)}" if status_parts else "Analysis complete: no issues found"
            self.state.set_status(status)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {playlist_path}: {e}")
            self.state.report_error(f"Failed to analyze {playlist_path.name}: {str(e)}")
            return None

    async def _detect_sort_method(self, valid_files: List[Path]) -> Optional[str]:
        """Detect the current sort method of the files."""
        if not valid_files:
            return None

        try:
            # Check path-based sorting
            paths_asc = sorted(valid_files)
            paths_desc = sorted(valid_files, reverse=True)

            if valid_files == paths_asc:
                return 'path_asc'
            if valid_files == paths_desc:
                return 'path_desc'

            # Check duration-based sorting
            try:
                durations = []
                for path in valid_files:
                    try:
                        audio = MP3(str(path))
                        durations.append((path, audio.info.length))
                    except Exception:
                        continue

                durations_asc = [p for p, _ in sorted(durations, key=lambda x: x[1])]
                durations_desc = [p for p, _ in sorted(durations, key=lambda x: x[1], reverse=True)]

                if valid_files == durations_asc:
                    return 'duration_asc'
                if valid_files == durations_desc:
                    return 'duration_desc'
            except Exception as e:
                self.logger.debug(f"Duration sort check failed: {e}")

            # Check BPM-based sorting
            try:
                def get_bpm(p):
                    try:
                        tags = EasyID3(str(p))
                        bpm = tags.get('bpm', [None])[0]
                        return float(bpm) if bpm else 0
                    except:
                        return 0

                bpm_asc = sorted(valid_files, key=get_bpm)
                bpm_desc = sorted(valid_files, key=get_bpm, reverse=True)

                if valid_files == bpm_asc:
                    return 'bpm_asc'
                if valid_files == bpm_desc:
                    return 'bpm_desc'
            except Exception as e:
                self.logger.debug(f"BPM sort check failed: {e}")

            # Allow events to process during sort detection
            await asyncio.sleep(0)

        except Exception as e:
            self.logger.error(f"Error detecting sort method: {e}")

        # No matching sort method found
        return None

    def analyze_playlist(self, playlist_path: Path):
        """Start analysis of a single playlist."""
        self.logger.info(f"Starting single playlist analysis: {playlist_path.name}")
        
        async def _analyze():
            self.state.is_analyzing = True
            self.state.analysis_started.emit(playlist_path)
            
            try:
                analysis = await self._analyze_playlist(playlist_path)
                if analysis:
                    self.logger.debug("Setting analysis result")
                    self.state.set_analysis(playlist_path, analysis)
                    
            except Exception as e:
                self.logger.error(f"Analysis failed: {str(e)}")
                self.state.report_error(f"Analysis failed: {str(e)}")
                
            finally:
                self.state.is_analyzing = False
                
        self._start_operation(
            _analyze(),
            progress_callback=self.state.update_progress
        )

    def analyze_all_playlists(self, playlists: List[Path]):
        """Start analysis of multiple playlists."""
        self.logger.info(f"Starting bulk analysis of {len(playlists)} playlists")

        async def _analyze_all():
            self.state.is_analyzing = True
            total = len(playlists)
            
            try:
                for i, playlist in enumerate(playlists, 1):
                    if not self.current_worker or not self.current_worker._is_running:
                        break
                        
                    progress = int((i - 1) / total * 100)
                    self.state.update_progress(progress)
                    
                    analysis = await self._analyze_playlist(playlist)
                    if analysis:
                        self.state.set_analysis(playlist, analysis)
                    
                    # Allow other events to process
                    await asyncio.sleep(0)
                    
                self.state.update_progress(100)
                self.state.set_status("Analysis complete")
                
            except Exception as e:
                self.logger.error(f"Bulk analysis failed: {e}")
                self.state.report_error(f"Analysis failed: {str(e)}")
                
            finally:
                self.state.is_analyzing = False
                self.state.analysis_all_completed.emit()

        self._start_operation(
            _analyze_all(),
            progress_callback=self.state.update_progress
        )

    def cleanup(self):
        """Clean up resources."""
        super().cleanup()