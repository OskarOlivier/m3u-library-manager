# tests/test_song_matcher.py
import unittest
from pathlib import Path
import win32gui
import win32process
import psutil
from core.matching.song_matcher import SongMatcher
from .conftest import get_playlist_dir

class TestSongMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = SongMatcher()
        self.playlists_dir = get_playlist_dir()
        self.music_dir = "E:/Albums"  # Base music directory
        
    def get_dopamine_window_title(self):
        """Get the current Dopamine window title"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name() == "Dopamine.exe":
                        title = win32gui.GetWindowText(hwnd)
                        if title and " - " in title:
                            windows.append(title)
                except psutil.NoSuchProcess:
                    pass
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None

    def test_current_playing_song(self):
        """Test matching with currently playing song in Dopamine"""
        window_title = self.get_dopamine_window_title()
        if not window_title:
            self.skipTest("No song playing in Dopamine or Dopamine not running")
        
        print(f"\nCurrent playing song: {window_title}")
        
        # Parse the window title
        parsed = self.matcher.parse_window_title(window_title)
        self.assertIsNotNone(parsed, "Failed to parse window title")
        
        artist, title = parsed
        print(f"Parsed artist: {artist}")
        print(f"Parsed title: {title}")
        
        # Find matches
        matches, playlists = self.matcher.find_matches(
            title=title,
            artist=artist,
            music_dir=self.music_dir,
            playlists_dir=str(self.playlists_dir)
        )
        
        # Print matching files
        print("\nMatching files:")
        for match in matches:
            print(f"  {match}")

        # Debug playlist checking
        print("\nChecking playlists:")
        playlist_files = list(Path(self.playlists_dir).glob("*.m3u"))
        print(f"Found {len(playlist_files)} playlist files")
        
        for playlist in playlist_files:
            print(f"\nChecking playlist: {playlist.name}")
            try:
                with open(playlist, 'r', encoding='utf-8') as f:
                    content = f.readlines()
                    print(f"  Contains {len(content)} entries")
                    
                    # Check if any matching file is in this playlist
                    for match in matches:
                        match_str = str(match)
                        found = False
                        for line_num, line in enumerate(content, 1):
                            if match_str in line.strip():
                                found = True
                                print(f"  Found match on line {line_num}:")
                                print(f"    Match: {match_str}")
                                print(f"    Line:  {line.strip()}")
                                break
                        if not found:
                            print(f"  Match not found: {match_str}")
                            # Show a few example lines from playlist for debugging
                            print("  Example playlist entries:")
                            for line in content[:3]:
                                print(f"    {line.strip()}")
                            
            except UnicodeDecodeError:
                print(f"  Failed to read with UTF-8, trying cp1252")
                try:
                    with open(playlist, 'r', encoding='cp1252') as f:
                        content = f.readlines()
                        print(f"  Contains {len(content)} entries (cp1252 encoding)")
                except Exception as e:
                    print(f"  Failed to read playlist: {e}")
            except Exception as e:
                print(f"  Error reading playlist: {e}")
        
        # Print summary
        print(f"\nTotal matches: {len(matches)} files in {len(playlists)} playlists")
        
        # Basic assertions
        self.assertGreaterEqual(len(matches), 0, "Should find at least one matching file")
        
        # Test path validity
        for match in matches:
            self.assertTrue(Path(match).exists(), f"Matched file does not exist: {match}")

if __name__ == '__main__':
    unittest.main()
