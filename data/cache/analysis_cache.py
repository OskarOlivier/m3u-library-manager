# data/cache/analysis_cache.py
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json
import logging
from data.models.analysis import AnalysisResult

class AnalysisCache:
    """Cache for playlist analysis results"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, AnalysisResult] = {}
        self._load_cache()
        
    def _get_cache_path(self, playlist_path: Path) -> Path:
        """Get cache file path for a playlist"""
        # Use hash of playlist path to avoid filesystem issues
        cache_name = f"{hash(str(playlist_path))}.json"
        return self.cache_dir / cache_name
        
    def _load_cache(self):
        """Load cached results from disk"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Convert stored data back to AnalysisResult
                    result = AnalysisResult(
                        playlist_path=Path(data['playlist_path']),
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        missing_remotely=[Path(p) for p in data['missing_remotely']],
                        missing_locally=[Path(p) for p in data['missing_locally']]
                    )
                    
                    # Only load if still valid
                    if result.is_valid:
                        self.results[str(result.playlist_path)] = result
                    else:
                        # Clean up expired cache files
                        cache_file.unlink()
                        
                except Exception as e:
                    logging.error(f"Error loading cache file {cache_file}: {e}")
                    # Remove corrupted cache file
                    cache_file.unlink(missing_ok=True)
                    
        except Exception as e:
            logging.error(f"Error loading analysis cache: {e}")
            
    def get_result(self, playlist_path: Path) -> Optional[AnalysisResult]:
        """Get cached result for a playlist if available and valid"""
        result = self.results.get(str(playlist_path))
        if result and result.is_valid:
            return result
        return None
        
    def store_result(self, playlist_path: Path, missing_remotely: list[Path], 
                    missing_locally: list[Path]):
        """Store analysis result in cache"""
        try:
            result = AnalysisResult(
                playlist_path=playlist_path,
                timestamp=datetime.now(),
                missing_remotely=missing_remotely,
                missing_locally=missing_locally
            )
            
            # Store in memory
            self.results[str(playlist_path)] = result
            
            # Store on disk
            cache_path = self._get_cache_path(playlist_path)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'playlist_path': str(playlist_path),
                    'timestamp': result.timestamp.isoformat(),
                    'missing_remotely': [str(p) for p in missing_remotely],
                    'missing_locally': [str(p) for p in missing_locally]
                }, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error storing analysis result: {e}")
            
    def clear_result(self, playlist_path: Path):
        """Clear cached result for a playlist"""
        try:
            # Remove from memory
            self.results.pop(str(playlist_path), None)
            
            # Remove from disk
            cache_path = self._get_cache_path(playlist_path)
            cache_path.unlink(missing_ok=True)
        except Exception as e:
            logging.error(f"Error clearing analysis result: {e}")
            
    def clear_all(self):
        """Clear all cached results"""
        try:
            self.results.clear()
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)
        except Exception as e:
            logging.error(f"Error clearing all analysis results: {e}")