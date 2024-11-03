# core/playlist/playlist_manager.py
from pathlib import Path
from typing import Optional, Tuple, List
from core.matching.song_matcher import SongMatcher
from core.common.file_utils import search_music_directory
from .operations import PlaylistOperations

class PlaylistManager:
    """Manages playlist operations and song toggling"""
    
    def __init__(self, music_dir: Path, playlists_dir: Path):
        self.music_dir = music_dir
        self.playlists_dir = playlists_dir
        self.matcher = SongMatcher()
        
    def toggle_song_in_playlist(self, playlist_path: Path, artist: str, title: str, include: bool) -> Tuple[bool, Optional[int]]:
        """
        Toggle song presence in playlist.
        Returns (success, new_track_count)
        """
        try:
            # Find matching files
            files = search_music_directory(
                artist=artist,
                title=title,
                music_dir=self.music_dir
            )
            
            if not files:
                return False, None
                
            file_str = str(files[0])
            success = False
            
            if include:
                success = PlaylistOperations.add_song_to_playlist(playlist_path, file_str)
            else:
                success = PlaylistOperations.remove_song_from_playlist(playlist_path, file_str)
                
            if success:
                new_count = PlaylistOperations.get_track_count(playlist_path)
                return True, new_count
                
            return False, None
            
        except Exception as e:
            print(f"Error toggling song in playlist: {e}")
            return False, None
            
    def get_song_playlists(self, artist: str, title: str) -> List[str]:
        """Get list of playlist names containing the specified song"""
        try:
            _, playlists = self.matcher.find_matches(
                title=title,
                artist=artist,
                music_dir=str(self.music_dir),
                playlists_dir=str(self.playlists_dir)
            )
            return playlists
        except Exception as e:
            print(f"Error getting song playlists: {e}")
            return []