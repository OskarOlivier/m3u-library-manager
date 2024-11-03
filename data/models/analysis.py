"""Analysis data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import List
from pathlib import Path

@dataclass
class AnalysisResult:
    """Stores analysis results."""
    playlist_path: Path
    timestamp: datetime
    missing_remotely: List[Path]
    missing_locally: List[Path]
    
    @property
    def is_valid(self) -> bool:
        """Check if analysis is still valid."""
        from app.config import Config
        return (datetime.now() - self.timestamp).seconds < Config.ANALYSIS_CACHE_DURATION
