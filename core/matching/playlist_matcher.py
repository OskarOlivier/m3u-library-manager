# core/matching/playlist_matcher.py

from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass
import os
import time
import logging

from utils.m3u.parser import read_m3u, _normalize_path

@dataclass
class PlaylistMatchResult:
    """Results of matching a file to playlists."""
    file_path: Path  # Original file path
    normalized_path: str  # Normalized path for matching
    playlists: List[str]  # Matching playlist names

class PlaylistMatcher:
    """Handles matching files to playlists using normalized path matching."""
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger('playlist_matcher')
        self.logger.setLevel(logging.DEBUG)
        
        # Add console handler if not present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def find_playlists_for_file(self, file_path: str, playlists_dir: str) -> List[str]:
        """
        Find playlists containing the specific file.
        
        Args:
            file_path: Path to the file to search for
            playlists_dir: Directory containing playlists
            
        Returns:
            List[str]: Names of playlists containing the file
        """
        
        start = time.perf_counter()
        
        try:
            # Normalize input path for consistent matching
            normalized_path = _normalize_path(file_path)
            matching_playlists = []
            
            # For each playlist in the configured directory
            playlists_path = Path(playlists_dir)
            if not playlists_path.exists():
                self.logger.warning("Playlists directory not found")
                return []
                
            from utils.playlist.stats import should_exclude_playlist
                
            for playlist in playlists_path.glob("*.m3u"):
                # Skip excluded playlists including Unplaylisted_*
                if should_exclude_playlist(playlist.name):
                    continue
                    
                try:
                    playlist_paths = read_m3u(str(playlist))
                    if playlist_paths is None:
                        self.logger.warning(f"Failed to read playlist: {playlist.name}")
                        continue
                        
                    # Check for match using normalized paths
                    if normalized_path in playlist_paths:
                        matching_playlists.append(playlist.name)
                        
                except Exception as e:
                    self.logger.error(f"Error processing playlist {playlist.name}: {e}")
                    continue
                        
            # Sort for consistent ordering
            matching_playlists.sort()
            
            self.logger.debug(f"Found {len(matching_playlists)} playlists containing {file_path}")
            return matching_playlists
                
        except Exception as e:
            self.logger.error(f"Error finding matching playlists: {e}")
            return []
            
        finally:
            duration = (time.perf_counter() - start) * 1000
            self.logger.debug(f"find_playlists_for_file took {duration:.2f}ms")
            
    def find_playlist_content(self, playlist_path: Path) -> Optional[Set[str]]:
        """
        Get normalized paths from a playlist file.
        
        Args:
            playlist_path: Path to playlist file
            
        Returns:
            Set of normalized paths if successful, None if failed
        """
        try:
            self.logger.debug(f"Reading playlist content: {playlist_path}")
            
            # read_m3u already returns normalized paths
            paths = read_m3u(str(playlist_path))
            if paths is None:
                self.logger.error(f"Failed to read playlist: {playlist_path}")
                return None
                
            # Convert to set for faster lookups
            path_set = set(paths)
            self.logger.debug(f"Found {len(path_set)} unique paths in playlist")
            
            return path_set
            
        except Exception as e:
            self.logger.error(f"Error reading playlist content: {e}", exc_info=True)
            return None
            
    def find_duplicates(self, playlist_path: Path) -> List[str]:
        """
        Find duplicate entries in a playlist using normalized paths.
        
        Args:
            playlist_path: Path to playlist file
            
        Returns:
            List of normalized paths that appear multiple times
        """
        try:
            self.logger.debug(f"Checking for duplicates in: {playlist_path}")
            
            # read_m3u already returns normalized paths
            paths = read_m3u(str(playlist_path))
            if paths is None:
                self.logger.error(f"Failed to read playlist: {playlist_path}")
                return []
                
            # Count occurrences
            path_counts = {}
            for path in paths:
                path_counts[path] = path_counts.get(path, 0) + 1
                
            # Find duplicates
            duplicates = [path for path, count in path_counts.items() if count > 1]
            
            if duplicates:
                self.logger.warning(f"Found {len(duplicates)} duplicate entries")
                for path in duplicates:
                    self.logger.debug(f"Duplicate path: {path} (appears {path_counts[path]} times)")
            else:
                self.logger.debug("No duplicates found")
                
            return duplicates
            
        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {e}", exc_info=True)
            return []