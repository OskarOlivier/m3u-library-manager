# core/matching/song_matcher.py

from pathlib import Path
from typing import List, Optional, Tuple, Dict, Set, Callable
from dataclasses import dataclass
import os
import re
from difflib import SequenceMatcher
import time
import logging

from core.common.string_utils import clean_for_matching, clean_for_probability, estimate_string_similarity

@dataclass
class SongMatchResult:
    """Results of matching a song to files."""
    artist: str
    title: str
    matches: List[Tuple[Path, float]]  # [(file_path, probability), ...]

class SongMatcher:
    """Finds matching files for a song based on artist and title."""
    
    def __init__(self):
        self.logger = logging.getLogger('song_matcher')
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def calculate_match_probability(self, file_path: str, artist: str, title: str) -> float:
        """Calculate probability of filename matching artist and title."""
        filename = file_path.split("\\")[3]
        
        try:
            # Parse filename (format: "E:\Albums\%album% - %albumtitle% (%year%)\%track% %artist% - %song%.mp3")
            try:
                file_name = Path(filename).stem
                if " - " not in file_name:
                    return 0.0

                file_artist = file_name.split(" - ")[0].split(" ", 1)[1]  # Skip track number
                file_title = file_name.split(" - ")[1]
                              
                # Calculate probabilities
                artist_prob = self._calculate_string_probability(artist, file_artist)
                title_prob = self._calculate_string_probability(title, file_title)
                
                # Combined probability (artist weighted more heavily)
                probability = (artist_prob * 0.4) + (title_prob * 0.6)
                                              
                return probability
                
            except Exception as e:
                self.logger.error(f"Error parsing filename: {e}")
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating probability: {e}")
            return 0.0

    def _calculate_string_probability(self, search: str, target: str) -> float:
        """Calculate match probability between search string and target."""
        # Clean strings keeping allowed special characters
        search_clean = clean_for_probability(search)
        target_clean = clean_for_probability(target)
        
        # Exact match after cleaning
        if search_clean == target_clean:
            return 1.0
            
        # Calculate similarity score
        return estimate_string_similarity(search_clean, target_clean)

    def find_matches(self, artist: str, title: str, music_dir: str, 
                    progress_callback: Optional[Callable[[int], None]] = None) -> List[Tuple[Path, float]]:
        """
        Find files matching the given artist and title.
        Returns list of (file_path, probability) tuples sorted by probability.
        
        Args:
            artist: Artist name to match
            title: Song title to match
            music_dir: Base music directory path
            progress_callback: Optional callback for progress updates (0-100)
        """
        start = time.perf_counter()
        
        try:
            if not title or not artist:
                return []

            matches = []
            high_confidence_match_found = False
            music_dir_path = Path(music_dir)

            # Phase 1: Direct folder + filename matching (0-50% progress)
            artist_clean = clean_for_matching(artist)
            total_folders = len(list(music_dir_path.iterdir()))
            processed_folders = 0
            
            for folder in music_dir_path.iterdir():
                if not folder.is_dir():
                    continue
                    
                # Check if folder name contains cleaned artist name
                if artist_clean not in clean_for_matching(folder.name):
                    continue
                    
                # Check mp3 files in folder and subfolders
                for file_path in folder.rglob("*.mp3"):
                    probability = self.calculate_match_probability(str(file_path), artist, title)
                    
                    if probability > 0.9:  # Save matches above 90%
                        matches.append((file_path, probability))
                        if probability > 0.95:  # Found high confidence match
                            high_confidence_match_found = True
                            
                processed_folders += 1
                if progress_callback:
                    progress = int((processed_folders / total_folders) * 50)  # 0-50% for phase 1
                    progress_callback(progress)

            # Phase 2: Fuzzy matching if no high confidence matches (50-100% progress)
            if not high_confidence_match_found:
                self.logger.debug("No high confidence matches found, starting fuzzy matching")
                search_string = f"{artist} - {title}"
                total_files = len(list(music_dir_path.rglob("*.mp3")))
                processed_files = 0
                
                for file_path in music_dir_path.rglob("*.mp3"):
                    search_path = file_path.stem.lower().split(' ', 1)[-1]
                    ratio = SequenceMatcher(None, search_string.lower(), search_path).ratio()
                    if ratio > 0.9:
                        matches.append((file_path, ratio))
                        
                    processed_files += 1
                    if progress_callback:
                        base_progress = 50  # Start at 50%
                        phase2_progress = int((processed_files / total_files) * 50)  # Additional 50%
                        progress_callback(base_progress + phase2_progress)

            matches.sort(key=lambda x: x[1], reverse=True)
            
            # Ensure final progress
            if progress_callback:
                progress_callback(100)
                
            return matches

        except Exception as e:
            self.logger.error(f"Error finding matches: {e}")
            return []
            
        finally:
            duration = (time.perf_counter() - start) * 1000
            self.logger.debug(f"find_matches took {duration:.2f}ms")