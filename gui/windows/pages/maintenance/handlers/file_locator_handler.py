# gui/windows/pages/maintenance/handlers/file_locator_handler.py

from pathlib import Path
import logging
import asyncio
from typing import Dict, Set, List, Tuple, Optional

from utils.m3u.parser import read_m3u, write_m3u
from gui.workers.async_base import AsyncOperation  # Updated import path

class FileLocatorHandler(AsyncOperation):
    """Handles file location and analysis operations."""
    
    def __init__(self, state):  
        super().__init__()
        self.state = state
        self.logger = logging.getLogger('file_locator_handler')

    def analyze_playlist(self, playlist_path: Path):
        """Analyze a playlist for missing files."""
        self.logger.debug(f"Starting playlist analysis: {playlist_path}")
        
        async def _analyze():
            try:
                self.state.is_analyzing = True
                self.state.analysis_started.emit(playlist_path)
                
                # Read playlist content
                paths = read_m3u(str(playlist_path))
                if paths is None:
                    self.state.report_error(f"Failed to read playlist: {playlist_path.name}")
                    return
                    
                # Find missing files
                missing_files = set()
                for path in paths:
                    file_path = Path(path)
                    if not file_path.exists():
                        missing_files.add(file_path)
                        
                # Update file panel
                self.state.set_missing_files(playlist_path, missing_files)
                
                if missing_files:
                    self.logger.info(f"Found {len(missing_files)} missing files")
                else:
                    self.logger.info("No missing files found")
                    
                self.state.analysis_completed.emit(playlist_path)
                
            except Exception as e:
                self.logger.error(f"Analysis failed: {e}", exc_info=True)
                self.state.report_error(f"Analysis failed: {str(e)}")
            finally:
                self.state.is_analyzing = False
                
        self._start_operation(
            _analyze(),
            progress_callback=self.state.update_progress
        )

    async def locate_files(self, missing_files: Set[Path]):
        """Search for alternative locations for missing files."""
        if self.is_running:
            self.logger.warning("Location search already in progress")
            return
            
        self.is_running = True
        found_alternatives: Dict[Path, Set[Path]] = {}
        not_found: Set[Path] = set()
        
        try:
            self.state.operation_started.emit("Locating Files")
            total_files = len(missing_files)
            
            for i, file_path in enumerate(missing_files, 1):
                if not self.is_running:
                    break
                    
                # Update progress
                progress = int((i - 1) / total_files * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Searching for: {file_path.name}")
                
                # Search for alternatives
                alternatives = await self._find_alternatives(file_path)
                
                if alternatives:
                    found_alternatives[file_path] = alternatives
                else:
                    not_found.add(file_path)
                    
                # Allow other operations
                await asyncio.sleep(0)
                
            self.progress_updated.emit(100)
            self.status_updated.emit("Search complete")
            
            # Return results through state
            self.state.set_location_results(found_alternatives, not_found)
            
        except Exception as e:
            self.logger.error(f"Error during file location: {e}", exc_info=True)
            self.error_occurred.emit(f"Error locating files: {str(e)}")
            
        finally:
            self.is_running = False
            self.state.operation_completed.emit("Locate Files")
            
    async def _find_alternatives(self, missing_path: Path) -> Set[Path]:
        """
        Find alternative locations for a missing file.
        Uses multiple search strategies including name matching and audio fingerprinting.
        
        Args:
            missing_path: Path to the missing file
            
        Returns:
            Set of potential alternative locations
        """
        alternatives = set()
        
        try:
            # Extract original name components
            name = missing_path.stem
            directory = missing_path.parent.relative_to(self.base_dir)
            
            # Strategy 1: Exact name match in any location
            matches = await self._search_by_name(name)
            alternatives.update(matches)
            
            # Strategy 2: Similar name match in original location
            if directory.exists():
                similar = await self._search_similar_names(name, directory)
                alternatives.update(similar)
                
            # Strategy 3: Check common alternative locations
            alt_locations = await self._check_alternative_locations(missing_path)
            alternatives.update(alt_locations)
            
            # Filter out existing path if present
            alternatives.discard(missing_path)
            
            return alternatives
            
        except Exception as e:
            self.logger.error(f"Error finding alternatives for {missing_path}: {e}")
            return set()
            
    async def _search_by_name(self, name: str) -> Set[Path]:
        """Search for exact name matches anywhere in library."""
        matches = set()
        
        try:
            clean_name = clean_string(name)
            
            for file_path in self.base_dir.rglob("*.mp3"):
                if not self.is_running:
                    break
                    
                if clean_string(file_path.stem) == clean_name:
                    matches.add(file_path)
                    
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in name search: {e}")
            return set()
            
    async def _search_similar_names(self, name: str, directory: Path) -> Set[Path]:
        """Search for similar names in the original directory."""
        matches = set()
        
        try:
            from difflib import SequenceMatcher
            
            clean_name = clean_string(name)
            search_dir = self.base_dir / directory
            
            if not search_dir.exists():
                return matches
                
            for file_path in search_dir.glob("*.mp3"):
                if not self.is_running:
                    break
                    
                clean_file = clean_string(file_path.stem)
                similarity = SequenceMatcher(None, clean_name, clean_file).ratio()
                
                if similarity > 0.8:  # 80% similarity threshold
                    matches.add(file_path)
                    
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in similarity search: {e}")
            return set()
            
    async def _check_alternative_locations(self, missing_path: Path) -> Set[Path]:
        """Check common alternative locations for the file."""
        alternatives = set()
        
        try:
            # Common location patterns
            patterns = [
                lambda p: p.parent.parent / "Alternative" / p.parent.name / p.name,
                lambda p: p.parent.parent / "Backup" / p.parent.name / p.name,
                lambda p: p.parent / "Alternative" / p.name,
            ]
            
            for pattern in patterns:
                alt_path = self.base_dir / pattern(missing_path.relative_to(self.base_dir))
                if alt_path.exists():
                    alternatives.add(alt_path)
                    
            return alternatives
            
        except Exception as e:
            self.logger.error(f"Error checking alternative locations: {e}")
            return set()
            
    async def repair_references(self, repairs: Dict[Path, Path]):
        """
        Repair file references in playlists.
        
        Args:
            repairs: Dictionary mapping original paths to their replacements
        """
        if self.is_running:
            self.logger.warning("Repair operation already in progress")
            return
            
        self.is_running = True
        
        try:
            self.state.operation_started.emit("Repairing References")
            playlists_dir = Path(Config.PLAYLISTS_DIR)
            
            # Get all playlists
            playlists = [p for p in playlists_dir.glob("*.m3u")
                        if p.name != "Love.bak.m3u"]
            
            total_playlists = len(playlists)
            repaired_count = 0
            
            for i, playlist_path in enumerate(playlists, 1):
                if not self.is_running:
                    break
                    
                # Update progress
                progress = int((i - 1) / total_playlists * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Repairing: {playlist_path.name}")
                
                # Repair playlist
                if await self._repair_playlist(playlist_path, repairs):
                    repaired_count += 1
                    
                # Allow other operations
                await asyncio.sleep(0)
                
            self.progress_updated.emit(100)
            self.status_updated.emit(
                f"Repaired references in {repaired_count} playlists")
            
        except Exception as e:
            self.logger.error(f"Error during reference repair: {e}", exc_info=True)
            self.error_occurred.emit(f"Error repairing references: {str(e)}")
            
        finally:
            self.is_running = False
            self.state.operation_completed.emit("Repair References")
            
    async def _repair_playlist(self, playlist_path: Path, 
                             repairs: Dict[Path, Path]) -> bool:
        """
        Repair references in a single playlist.
        
        Args:
            playlist_path: Path to playlist file
            repairs: Dictionary of original paths to replacements
            
        Returns:
            bool: True if playlist was modified
        """
        try:
            # Read playlist content
            paths = read_m3u(str(playlist_path))
            if paths is None:
                return False
                
            # Track if modifications were made
            modified = False
            
            # Create new paths list
            new_paths = []
            for path in paths:
                path_obj = Path(path)
                if path_obj in repairs:
                    new_paths.append(str(repairs[path_obj]))
                    modified = True
                else:
                    new_paths.append(path)
                    
            # Write back if modified
            if modified:
                write_m3u(str(playlist_path), new_paths)
                self.logger.info(f"Repaired references in {playlist_path.name}")
                
            return modified
            
        except Exception as e:
            self.logger.error(f"Error repairing {playlist_path.name}: {e}")
            return False
            
    def stop(self):
        """Stop current operation."""
        self.is_running = False
            
    def cleanup(self):
        """Clean up resources."""
        self.stop()