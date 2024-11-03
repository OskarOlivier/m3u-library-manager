import unittest
from pathlib import Path
import tempfile
import shutil
import os
from core.matching.song_matcher import SongMatcher
from core.playlist.operations import find_missing_files, validate_playlist, clean_playlist
from utils.m3u.parser import read_m3u, write_m3u
from .conftest import get_playlist_dir

class TestPlaylistOperations(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.matcher = SongMatcher()
        self.playlists_dir = get_playlist_dir()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Find test playlists
        self.test_playlists = list(self.playlists_dir.glob("*.m3u"))[:3]
        
        if not self.test_playlists:
            self.skipTest("No M3U files found in playlist directory")
            
        print(f"\nFound {len(self.test_playlists)} test playlists:")
        for playlist in self.test_playlists:
            print(f"- {playlist.name}")
            
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_playlist_reading(self):
        """Test reading playlist files"""
        for playlist in self.test_playlists:
            print(f"\nReading playlist: {playlist.name}")
            paths = read_m3u(str(playlist))
            
            self.assertIsNotNone(paths)
            self.assertIsInstance(paths, list)
            print(f"Found {len(paths)} entries")
            
            # Show sample of entries
            for path in paths[:3]:
                print(f"- {Path(path).name}")
            if len(paths) > 3:
                print("...")

    def test_playlist_validation(self):
        """Test playlist validation features"""
        for playlist in self.test_playlists:
            print(f"\nValidating playlist: {playlist.name}")
            paths = read_m3u(str(playlist))
            
            # Test missing files detection
            missing = find_missing_files(paths)
            print(f"Missing files: {len(missing)}")
            for line_num, path in missing[:3]:
                print(f"- Line {line_num}: {Path(path).name}")
            
            # Test validation
            errors = validate_playlist(str(playlist), paths)
            print(f"Validation errors: {len(errors)}")
            for error in errors[:3]:
                print(f"- {error}")

    def test_playlist_cleaning(self):
        """Test playlist cleaning operations"""
        for playlist in self.test_playlists:
            print(f"\nCleaning playlist: {playlist.name}")
            paths = read_m3u(str(playlist))
            
            # Create test playlist with duplicates
            test_playlist = self.temp_dir / playlist.name
            with open(test_playlist, 'w', encoding='utf-8') as f:
                # Add some paths twice
                for path in paths:
                    f.write(f"{path}\n")
                    f.write(f"{path}\n")  # Duplicate
                f.write("\n")  # Empty line
            
            # Read and clean
            dirty_paths = read_m3u(str(test_playlist))
            cleaned_paths = clean_playlist(dirty_paths)
            
            print(f"Original entries: {len(dirty_paths)}")
            print(f"After cleaning: {len(cleaned_paths)}")
            print(f"Removed: {len(dirty_paths) - len(cleaned_paths)} entries")
            
            # Verify no duplicates remain
            self.assertEqual(len(cleaned_paths), len(set(cleaned_paths)))

    def test_song_matching(self):
        """Test song matching in playlists"""
        # Find a test file from first playlist
        if not self.test_playlists:
            self.skipTest("No playlists available")
            
        paths = read_m3u(str(self.test_playlists[0]))
        if not paths:
            self.skipTest("Empty playlist")
            
        test_path = Path(paths[0])
        if not test_path.exists():
            self.skipTest("No valid files in playlist")
            
        print(f"\nTesting with file: {test_path.name}")
        
        # Try to format as window title
        title_parts = test_path.stem.split(" - ", 1)
        if len(title_parts) == 2:
            artist, title = title_parts
            window_title = f"{artist} - {title}"
            print(f"Testing window title: {window_title}")
            
            # Find matches
            matches, playlists = self.matcher.find_matches_from_window_title(
                window_title,
                str(test_path.parent),
                str(self.playlists_dir)
            )
            
            self.assertGreater(len(matches), 0, "Should find at least one match")
            print(f"\nFound {len(matches)} matching files in {len(playlists)} playlists")
            
            for playlist in playlists:
                print(f"- Present in: {playlist}")

    def test_playlist_modification(self):
        """Test modifying playlist contents"""
        if not self.test_playlists:
            self.skipTest("No test playlists")
            
        source_playlist = self.test_playlists[0]
        test_playlist = self.temp_dir / "test.m3u"
        
        # Copy playlist for testing
        shutil.copy2(source_playlist, test_playlist)
        
        print(f"\nTesting modifications on: {test_playlist.name}")
        
        # Read original content
        original_paths = read_m3u(str(test_playlist))
        print(f"Original entries: {len(original_paths)}")
        
        # Test removal
        if original_paths:
            modified_paths = original_paths[1:]
            write_m3u(str(test_playlist), modified_paths)
            
            # Verify
            new_paths = read_m3u(str(test_playlist))
            self.assertEqual(len(new_paths), len(original_paths) - 1)
            print(f"After removal: {len(new_paths)} entries")
            
            # Test addition
            write_m3u(str(test_playlist), original_paths)
            final_paths = read_m3u(str(test_playlist))
            self.assertEqual(len(final_paths), len(original_paths))
            print(f"After restoring: {len(final_paths)} entries")

if __name__ == '__main__':
    unittest.main()
