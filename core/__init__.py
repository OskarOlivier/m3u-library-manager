# core/cache/__init__.py

"""Cache package initialization and management."""
from pathlib import Path
import logging
from typing import Optional

from .cache.relationship_cache import RelationshipCache

# Initialize package-level logger
logger = logging.getLogger(__name__)

class CacheManager:
    """Manages cache initialization and cleanup across components."""
    
    _instance = None
    
    def __init__(self):
        if CacheManager._instance is not None:
            raise RuntimeError("CacheManager is a singleton - use get_instance()")
            
        self.relationship_cache = RelationshipCache.get_instance()
        self._initialized = False
        
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = CacheManager()
        return cls._instance
        
    async def initialize_caches(self, playlists_dir: Path, 
                              progress_callback: Optional[callable] = None) -> None:
        """Initialize all cache components."""
        if self._initialized:
            logger.warning("Caches already initialized")
            return
            
        try:
            logger.info("Initializing cache components")
            
            # Initialize relationship cache
            await self.relationship_cache.initialize(playlists_dir, progress_callback)
            
            self._initialized = True
            logger.info("Cache initialization complete")
            
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}", exc_info=True)
            self.cleanup()
            raise
            
    def cleanup(self) -> None:
        """Clean up all cache components."""
        try:
            logger.info("Cleaning up cache components")
            
            # Access internal clear method for relationship cache
            if hasattr(self.relationship_cache, '_clear_cache'):
                self.relationship_cache._clear_cache()
                
            self._initialized = False
            logger.info("Cache cleanup complete")
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}", exc_info=True)
            
    @property
    def is_initialized(self) -> bool:
        """Check if caches are initialized."""
        return self._initialized

__all__ = ['RelationshipCache', 'CacheManager']