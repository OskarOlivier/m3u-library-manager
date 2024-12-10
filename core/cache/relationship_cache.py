# core/cache/relationship_cache.py

from core.cache.base import CacheBase
from core.events.event_bus import EventBus, EventType
from pathlib import Path
from typing import Dict, Set, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
import asyncio
from collections import defaultdict

from utils.m3u.parser import read_m3u, _normalize_path


@dataclass
class RelationshipMetrics:
    """Stores the relationship strength between two playlists."""
    intersection_size: int    # Number of tracks in common
    source_size: int         # Total tracks in source playlist
    target_size: int         # Total tracks in target playlist
    
    @property
    def normalized_score(self) -> float:
        """Get normalized relationship score (0-1)."""
        if self.source_size == 0 or self.target_size == 0:
            return 0.0
        #return self.intersection_size / min(self.source_size, self.target_size)
        return self.intersection_size
    
    @property
    def has_relationship(self) -> bool:
        """Check if playlists have any relationship."""
        return self.intersection_size > 0


class RelationshipCache(CacheBase):
    """Manages cached relationship data between playlists."""
    
    _instance = None
    
    def __init__(self):
        super().__init__()
        self.name = "relationship_cache"
        self._cache: Dict[str, Dict[str, RelationshipMetrics]] = {}
        self._track_to_playlists: Dict[str, Set[str]] = defaultdict(set)
        self._playlist_tracks: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger('relationship_cache')
        self.event_bus = EventBus.get_instance()
        self._initialization_lock = asyncio.Lock()
        self._initialization_started = False

    @classmethod
    def get_instance(cls) -> 'RelationshipCache':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = RelationshipCache()
        return cls._instance

    async def initialize(self, playlists_dir: Path, 
                        progress_callback: Optional[callable] = None) -> None:
        """Initialize cache with all playlists asynchronously."""
        async with self._initialization_lock:
            if self._initialized:
                self.logger.warning("Cache already initialized")
                return
                
            if self._initialization_started:
                self.logger.debug("Initialization already in progress")
                return
                
            self._initialization_started = True
            
            try:
                self.logger.info("Starting cache initialization")
                self._clear_cache()
                
                # Get regular playlists (excluding backups and unplaylisted)
                from utils.playlist import get_regular_playlists
                playlist_paths = get_regular_playlists(playlists_dir)
                total_playlists = len(playlist_paths)
                
                if not playlist_paths:
                    self.logger.warning("No playlists found for initialization")
                    return

                # First pass: Load all playlist tracks
                for i, playlist_path in enumerate(playlist_paths):
                    if progress_callback:
                        progress = int((i / total_playlists) * 50)  # First 50%
                        progress_callback(progress)
                        
                    try:
                        tracks = read_m3u(str(playlist_path))
                        if tracks is None:
                            continue
                            
                        normalized_tracks = {_normalize_path(t) for t in tracks}
                        playlist_id = str(playlist_path)
                        
                        # Store playlist tracks
                        self._playlist_tracks[playlist_id] = normalized_tracks
                        
                        # Update track to playlist mapping
                        for track in normalized_tracks:
                            self._track_to_playlists[track].add(playlist_id)
                            
                        self.logger.debug(f"Loaded {len(normalized_tracks)} tracks for {playlist_path.name}")
                            
                    except Exception as e:
                        self.logger.error(f"Error loading playlist {playlist_path}: {e}")
                        continue
                        
                    await asyncio.sleep(0)
                    
                # Second pass: Calculate relationships
                self.logger.info("Calculating playlist relationships")
                for i, source_id in enumerate(self._playlist_tracks):
                    if progress_callback:
                        progress = 50 + int((i / total_playlists) * 50)  # Second 50%
                        progress_callback(progress)
                        
                    source_tracks = self._playlist_tracks[source_id]
                    source_size = len(source_tracks)
                    
                    self._cache[source_id] = {}
                    
                    MIN_INTERSECTION_THRESHOLD = 1  # Example: At least 3 shared tracks
                    
                    # Calculate relationships with other playlists
                    for target_id, target_tracks in self._playlist_tracks.items():
                        if source_id != target_id:
                            intersection = source_tracks & target_tracks
                            intersection_size = len(intersection)
                            target_size = len(target_tracks)
                            
                            # Only store if there's a relationship
                            if intersection_size > MIN_INTERSECTION_THRESHOLD:
                                metrics = RelationshipMetrics(
                                    intersection_size=intersection_size,
                                    source_size=source_size,
                                    target_size=target_size
                                )
                                
                                self._cache[source_id][target_id] = metrics
                                
                                self.logger.debug(
                                    f"Found relationship: {Path(source_id).name} -> {Path(target_id).name} "
                                    f"({intersection_size} shared tracks, score: {metrics.normalized_score:.2f})"
                                )
                            
                    await asyncio.sleep(0)
                    
                if progress_callback:
                    progress_callback(100)
                    
                self._initialized = True
                self._initialization_started = False
                
                self.logger.info(f"Cache initialization complete. Found {len(self._track_to_playlists)} unique tracks "
                               f"across {len(self._playlist_tracks)} playlists")
                
                self._set_initialized()  # Use base class method
                
                # Emit cache ready event
                self.event_bus.emit_event(EventType.CACHE_READY, {
                    'cache_type': 'relationship',
                    'playlist_count': len(self._playlist_tracks),
                    'track_count': len(self._track_to_playlists)
                })
                
            except Exception as e:
                self._initialization_started = False
                self._initialized = False
                self._report_error(f"Cache initialization failed: {e}")
                raise

    def is_initialization_started(self) -> bool:
        """Check if initialization has started."""
        return self._initialization_started
            
    def _clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._track_to_playlists.clear()
        self._playlist_tracks.clear()
        self._initialized = False
        
    def get_related_playlists(self, playlist_id: str, 
                             threshold: float = 0.0,
                             limit: Optional[int] = None) -> Dict[str, float]:
        """Get playlists related to the given playlist with their relationship strengths."""
        if not self._initialized:
            self.logger.warning("Cache not initialized")
            return {}
            
        if playlist_id not in self._cache:
            self.logger.warning(f"Playlist not found in cache: {playlist_id}")
            return {}
            
        # Get all relationships 
        relationships = {
            target_id: metrics.normalized_score
            for target_id, metrics in self._cache[playlist_id].items()
            if metrics.intersection_size > 0 and metrics.normalized_score >= threshold
        }
        
        self.logger.debug(f"Found {len(relationships)} relationships for {Path(playlist_id).name}")
        
        # Sort by strength and apply limit
        sorted_relationships = dict(
            sorted(relationships.items(), 
                  key=lambda x: x[1], 
                  reverse=True)[:limit]
        )
        
        return sorted_relationships
        
    def get_relationship_metrics(self, source_id: str, 
                               target_id: str) -> Optional[RelationshipMetrics]:
        """Get detailed relationship metrics between two playlists."""
        if not self._initialized:
            return None
        return self._cache.get(source_id, {}).get(target_id)
        
    def get_common_tracks(self, source_id: str, target_id: str) -> Set[str]:
        """Get set of tracks common to both playlists."""
        if not self._initialized:
            return set()
            
        source_tracks = self._playlist_tracks.get(source_id, set())
        target_tracks = self._playlist_tracks.get(target_id, set())
        return source_tracks & target_tracks
        
    def get_playlists_containing_track(self, track_path: str) -> Set[str]:
        """Get playlists that contain a specific track."""
        if not self._initialized:
            return set()
            
        normalized_path = _normalize_path(track_path)
        return self._track_to_playlists.get(normalized_path, set())
        
    async def update_playlist(self, playlist_id: str, tracks: Set[str]) -> None:
        """Update cache for a modified playlist."""
        if not self._initialized:
            return
            
        try:
            # Normalize all tracks
            normalized_tracks = {_normalize_path(t) for t in tracks}
            
            # Get old tracks for cleanup
            old_tracks = self._playlist_tracks.get(playlist_id, set())
            
            # Update playlist tracks
            self._playlist_tracks[playlist_id] = normalized_tracks
            
            # Update track to playlist mapping
            for track in old_tracks - normalized_tracks:
                self._track_to_playlists[track].discard(playlist_id)
                if not self._track_to_playlists[track]:
                    del self._track_to_playlists[track]
                    
            for track in normalized_tracks:
                self._track_to_playlists[track].add(playlist_id)
                
            # Recalculate relationships
            source_size = len(normalized_tracks)
            self._cache[playlist_id] = {}
            
            for target_id, target_tracks in self._playlist_tracks.items():
                if playlist_id != target_id:
                    intersection = normalized_tracks & target_tracks
                    intersection_size = len(intersection)
                    target_size = len(target_tracks)
                    
                    # Only store if there's a relationship
                    if intersection_size > 0:
                        metrics = RelationshipMetrics(
                            intersection_size=intersection_size,
                            source_size=source_size,
                            target_size=target_size
                        )
                        
                        self._cache[playlist_id][target_id] = metrics
                        
                    # Allow other operations
                    await asyncio.sleep(0)
                    
            self.logger.debug(f"Updated cache for playlist: {playlist_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating cache for {playlist_id}: {e}")
            
    def remove_playlist(self, playlist_id: str) -> None:
        """Remove a playlist from the cache."""
        if not self._initialized():
            return
            
        try:
            # Remove from playlist tracks
            old_tracks = self._playlist_tracks.pop(playlist_id, set())
            
            # Update track to playlist mapping
            for track in old_tracks:
                self._track_to_playlists[track].discard(playlist_id)
                if not self._track_to_playlists[track]:
                    del self._track_to_playlists[track]
                    
            # Remove from relationships cache
            self._cache.pop(playlist_id, None)
            for relationships in self._cache.values():
                relationships.pop(playlist_id, None)
                
            self.logger.debug(f"Removed playlist from cache: {playlist_id}")
            
        except Exception as e:
            self.logger.error(f"Error removing playlist {playlist_id}: {e}")