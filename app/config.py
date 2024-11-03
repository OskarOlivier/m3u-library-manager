"""Application-wide configuration."""
from pathlib import Path

class Config:
    """Global configuration settings."""
    
    # Paths
    LOCAL_BASE = Path(r"E:\Albums")
    PLAYLISTS_DIR = Path(r"D:\Music\Dopamine\Playlists")
    BACKUP_DIR = PLAYLISTS_DIR / "backups"
    
    # SSH Settings
    SSH_HOST = "192.168.178.43"
    SSH_USERNAME = "pi"
    SSH_REMOTE_PATH = "/media/CHIA/Music"
    
    # Cache Settings
    ANALYSIS_CACHE_DURATION = 3600  # 1 hour in seconds
