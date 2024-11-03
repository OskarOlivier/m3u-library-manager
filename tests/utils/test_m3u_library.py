# tests/test_m3u_library.py
import unittest
import os
from pathlib import Path
from .conftest import get_playlist_dir

from utils.m3u.parser import read_m3u, write_m3u, convert_path_separators, M3UParseError
from utils.m3u.path_utils import is_absolute_path, make_absolute, make_relative, verify_library_path
from core.playlist.operations import find_missing_files, validate_playlist, clean_playlist

class TestM3ULibrary(unittest.TestCase):
    def setUp(self):
        """Set up test environment using real playlists"""
        self.playlists_dir = get_playlist_dir()
        self.playlists = list(self.playlists_dir.glob("*.m3u"))
        self.playlists.extend(self.playlists_dir.glob("*.m3u8"))
        
        if not self.playlists:
            self.skipTest("No M3U/M3U8 files found in playlist directory")
        
        print(f"\nFound {len(self.playlists)} playlist files:")
        for playlist in self.playlists:
            print(f"- {playlist.name}")

    def test_read_playlists(self):
        """Test reading all playlists"""
        for playlist in self.playlists:
            print(f"\nReading playlist: {playlist.name}")
            try:
                paths = read_m3u(str(playlist))
                self.assertIsNotNone(paths, f"Failed to read {playlist.name}")
                print(f"Successfully read {len(paths)} entries")
                
                # Show first few entries
                for i, path in enumerate(paths[:3], 1):
                    print(f"  {i}. {path}")
                if len(paths) > 3:
                    print("  ...")
                    
            except M3UParseError as e:
                self.fail(f"Failed to parse {playlist.name}: {e}")

    def test_find_missing_tracks(self):
        """Test finding missing files in all playlists"""
        for playlist in self.playlists:
            print(f"\nChecking missing files in: {playlist.name}")
            paths = read_m3u(str(playlist))
            missing = find_missing_files(paths)
            
            print(f"Found {len(missing)} missing files out of {len(paths)} total tracks")
            
            # Show some examples of missing files
            for i, (line_num, path) in enumerate(missing[:3], 1):
                print(f"  {i}. Line {line_num}: {path}")
            if len(missing) > 3:
                print("  ...")

    def test_path_types(self):
        """Analyze path types in playlists"""
        for playlist in self.playlists:
            print(f"\nAnalyzing paths in: {playlist.name}")
            paths = read_m3u(str(playlist))
            
            absolute_paths = [p for p in paths if is_absolute_path(p)]
            relative_paths = [p for p in paths if not is_absolute_path(p)]
            
            print(f"Total paths: {len(paths)}")
            print(f"Absolute paths: {len(absolute_paths)}")
            print(f"Relative paths: {len(relative_paths)}")
            
            # Show examples of each type
            if absolute_paths:
                print("\nExample absolute paths:")
                for path in absolute_paths[:2]:
                    print(f"  {path}")
            if relative_paths:
                print("\nExample relative paths:")
                for path in relative_paths[:2]:
                    print(f"  {path}")

    def test_clean_playlists(self):
        """Test cleaning all playlists"""
        for playlist in self.playlists:
            print(f"\nCleaning playlist: {playlist.name}")
            paths = read_m3u(str(playlist))
            
            original_count = len(paths)
            cleaned_paths = clean_playlist(paths)
            cleaned_count = len(cleaned_paths)
            
            print(f"Original entries: {original_count}")
            print(f"After cleaning: {cleaned_count}")
            print(f"Removed: {original_count - cleaned_count} duplicates/empty lines")

    def test_validate_playlists(self):
        """Validate all playlists"""
        for playlist in self.playlists:
            print(f"\nValidating playlist: {playlist.name}")
            paths = read_m3u(str(playlist))
            errors = validate_playlist(str(playlist), paths)
            
            if errors:
                print(f"Found {len(errors)} issues:")
                for i, error in enumerate(errors[:5], 1):
                    print(f"  {i}. {error}")
                if len(errors) > 5:
                    print(f"  ... and {len(errors) - 5} more issues")
            else:
                print("No issues found")

    def test_library_format(self):
        """Check if paths follow the library format"""
        for playlist in self.playlists:
            print(f"\nChecking library format in: {playlist.name}")
            paths = read_m3u(str(playlist))
            
            invalid_paths = []
            for path in paths:
                if error := verify_library_path(path):
                    invalid_paths.append((path, error))
            
            print(f"Checked {len(paths)} paths")
            print(f"Found {len(invalid_paths)} non-standard paths")
            
            # Show examples of non-standard paths
            for path, error in invalid_paths[:3]:
                print(f"  Invalid path: {path}")
                print(f"  Reason: {error}")
            if len(invalid_paths) > 3:
                print("  ...")

if __name__ == '__main__':
    unittest.main()
