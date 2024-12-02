# core/services/analysis_service.py

from pathlib import Path
from typing import Optional, Dict, Set, List, Tuple, Callable
import logging
import asyncio
from dataclasses import dataclass

from core.context import ServiceProvider
from core.sync.file_comparator import ComparisonResult
from core.matching.song_matcher import SongMatchResult
from core.common.string_utils import clean_for_matching
from utils.m3u.parser import read_m3u, write_m3u
from utils.id3.reader import get_id3_tags
from utils.id3.writer import write_id3_tags

@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    path: Path
    exists: bool
    size: Optional[int] = None
    id3_tags: Optional[Dict[str, str]] = None
    duration: Optional[float] = None
    bpm: Optional[float] = None
    has_errors: bool = False
    error_message: Optional[str] = None

@dataclass
class PlaylistAnalysis:
    """Analysis results for a playlist."""
    path: Path
    track_count: int
    exists_remotely: bool
    missing_files: Set[Path]
    duplicate_files: Set[Path]
    invalid_paths: Set[Path]
    file_analyses: Dict[Path, FileAnalysis]
    sort_method: Optional[str] = None

class AnalysisService(ServiceProvider):
    """Centralized service for file and playlist analysis."""

    def __init__(self):
        super().__init__("analysis_service")
        self._cache: Dict[Path, PlaylistAnalysis] = {}
        self._is_analyzing = False

    async def initialize(self) -> None:
        """Initialize the analysis service."""
        self.logger.debug("Initializing analysis service")
        pass

    async def start(self) -> None:
        """Start the analysis service."""
        self.logger.debug("Starting analysis service")
        pass

    async def stop(self) -> None:
        """Stop the analysis service."""
        self.logger.debug("Stopping analysis service")
        self._is_analyzing = False
        self._cache.clear()

    def get_cached_analysis(self, playlist_path: Path) -> Optional[PlaylistAnalysis]:
        """Get cached analysis results for a playlist."""
        return self._cache.get(playlist_path)

    async def analyze_playlist(self, playlist_path: Path, 
                             progress_callback: Optional[Callable[[int], None]] = None) -> Optional[PlaylistAnalysis]:
        """Perform comprehensive playlist analysis."""
        try:
            self._is_analyzing = True
            if progress_callback:
                progress_callback(0)

            # Read playlist content
            tracks = read_m3u(str(playlist_path))
            if not tracks:
                return None

            # Initialize analysis containers
            missing_files = set()
            duplicate_files = set()
            invalid_paths = set()
            file_analyses = {}
            track_count = len(tracks)

            # Analyze each file
            for i, track_path in enumerate(tracks):
                path = Path(track_path)
                
                # Update progress
                if progress_callback:
                    progress = int((i / track_count) * 80)  # Save 20% for final steps
                    progress_callback(progress)

                # Analyze file
                analysis = await self._analyze_file(path)
                file_analyses[path] = analysis

                # Track issues
                if not analysis.exists:
                    missing_files.add(path)
                if analysis.has_errors:
                    invalid_paths.add(path)

            # Check for duplicates
            seen_paths = set()
            for track in tracks:
                if track in seen_paths:
                    duplicate_files.add(Path(track))
                seen_paths.add(track)

            # Determine sort method
            sort_method = await self._detect_sort_method(tracks, file_analyses)

            # Final progress
            if progress_callback:
                progress_callback(90)

            # Create analysis result
            analysis = PlaylistAnalysis(
                path=playlist_path,
                track_count=track_count,
                exists_remotely=True,  # Will be updated by sync analysis
                missing_files=missing_files,
                duplicate_files=duplicate_files,
                invalid_paths=invalid_paths,
                file_analyses=file_analyses,
                sort_method=sort_method
            )

            # Cache result
            self._cache[playlist_path] = analysis

            # Complete progress
            if progress_callback:
                progress_callback(100)

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing playlist {playlist_path}: {e}")
            return None
        finally:
            self._is_analyzing = False

    async def _analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file."""
        try:
            exists = file_path.exists()
            if not exists:
                return FileAnalysis(path=file_path, exists=False)

            size = file_path.stat().st_size
            
            # Get ID3 tags
            id3_tags = get_id3_tags(str(file_path))
            
            # Get duration and BPM if available
            duration = None
            bpm = None
            if id3_tags:
                if 'TLEN' in id3_tags:  # Duration in milliseconds
                    try:
                        duration = float(id3_tags['TLEN'][0]) / 1000
                    except (ValueError, IndexError):
                        pass
                if 'TBPM' in id3_tags:  # BPM
                    try:
                        bpm = float(id3_tags['TBPM'][0])
                    except (ValueError, IndexError):
                        pass

            return FileAnalysis(
                path=file_path,
                exists=True,
                size=size,
                id3_tags=id3_tags,
                duration=duration,
                bpm=bpm
            )

        except Exception as e:
            return FileAnalysis(
                path=file_path,
                exists=file_path.exists(),
                has_errors=True,
                error_message=str(e)
            )

    async def _detect_sort_method(self, tracks: List[str], 
                                analyses: Dict[Path, FileAnalysis]) -> Optional[str]:
        """Detect the current sort method of the playlist."""
        if not tracks:
            return None

        # Check if sorted by path
        paths_sorted = sorted(tracks)
        if tracks == paths_sorted:
            return 'path_asc'
        if tracks == list(reversed(paths_sorted)):
            return 'path_desc'

        # Check if sorted by duration
        if all(a.duration for a in analyses.values()):
            durations = [(p, a.duration) for p, a in analyses.items()]
            duration_sorted = [p for p, _ in sorted(durations, key=lambda x: x[1])]
            if tracks == duration_sorted:
                return 'duration_asc'
            if tracks == list(reversed(duration_sorted)):
                return 'duration_desc'

        # Check if sorted by BPM
        if all(a.bpm for a in analyses.values()):
            bpms = [(p, a.bpm) for p, a in analyses.items()]
            bpm_sorted = [p for p, _ in sorted(bpms, key=lambda x: x[1])]
            if tracks == bpm_sorted:
                return 'bpm_asc'
            if tracks == list(reversed(bpm_sorted)):
                return 'bpm_desc'

        return 'custom'

    async def find_music_files(self, file_path: Path, possible_locations: List[Path],
                             match_threshold: float = 0.9) -> List[Tuple[Path, float]]:
        """Find possible matches for a music file in different locations."""
        matches = []
        base_name = clean_for_matching(file_path.stem)

        for location in possible_locations:
            try:
                for candidate in location.rglob("*.mp3"):
                    # Clean names for matching
                    candidate_name = clean_for_matching(candidate.stem)
                    
                    # Calculate similarity
                    from core.common.string_utils import estimate_string_similarity
                    similarity = estimate_string_similarity(base_name, candidate_name)
                    
                    if similarity >= match_threshold:
                        matches.append((candidate, similarity))

            except Exception as e:
                self.logger.error(f"Error searching location {location}: {e}")
                continue

        # Sort by similarity
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def cleanup(self) -> None:
        """Clean up service resources."""
        try:
            self._cache.clear()
            self._is_analyzing = False
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")