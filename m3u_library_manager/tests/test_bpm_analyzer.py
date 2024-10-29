import unittest
import os
from pathlib import Path
import tempfile
import shutil
import hashlib
import contextlib
from mutagen.easyid3 import EasyID3
from core.analysis.bpm_analyzer import BPMAnalyzer
from .conftest import get_playlist_dir

class SafetyError(Exception):
    """Raised when a safety check fails"""
    pass

@contextlib.contextmanager
def safe_test_file(original_path: Path):
    """Safely handle test file creation and cleanup"""
    temp_dir = None
    temp_path = None
    original_hash = hashlib.md5(original_path.read_bytes()).hexdigest()
    original_tags = dict(EasyID3(str(original_path))) if original_path.exists() else {}
    
    try:
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir) / original_path.name
        shutil.copy2(original_path, temp_path)
        yield temp_path
    finally:
        if temp_path and temp_path.exists():
            current_hash = hashlib.md5(original_path.read_bytes()).hexdigest()
            if current_hash != original_hash:
                raise SafetyError("Original file was modified!")
            try:
                current_tags = dict(EasyID3(str(original_path)))
                if current_tags != original_tags:
                    raise SafetyError("Original ID3 tags were modified!")
            except:
                pass
            temp_path.unlink(missing_ok=True)
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

class TestBPMAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = BPMAnalyzer()
        self.playlists_dir = get_playlist_dir()
        
        # Find multiple test files from playlists
        self.test_files = []
        for playlist in self.playlists_dir.glob("*.m3u"):
            with open(playlist, 'r', encoding='utf-8') as f:
                for line in f:
                    path = Path(line.strip())
                    if path.exists() and path.suffix.lower() == '.mp3':
                        self.test_files.append(path)
                        if len(self.test_files) >= 5:  # Test with 5 different files
                            break
            if len(self.test_files) >= 5:
                break
                
        if not self.test_files:
            self.skipTest("No MP3 files found in playlists")
            
        print(f"\nFound {len(self.test_files)} test files:")
        for file in self.test_files:
            print(f"- {file.name}")

    def test_bpm_consistency(self):
        """Test if BPM detection is consistent across multiple runs"""
        for test_file in self.test_files:
            print(f"\nTesting BPM consistency for: {test_file.name}")
            with safe_test_file(test_file) as temp_path:
                # Run analysis multiple times
                results = []
                for _ in range(3):
                    bpm, error = self.analyzer.analyze_file(temp_path)
                    if bpm:
                        results.append(bpm)
                
                if results:
                    print(f"BPM readings: {results}")
                    # Check if all results are within 1 BPM of each other
                    self.assertTrue(max(results) - min(results) <= 1,
                                  "BPM detection not consistent")

    def test_existing_bpm_tag(self):
        """Test handling of files with existing BPM tags"""
        for test_file in self.test_files:
            print(f"\nTesting existing BPM handling for: {test_file.name}")
            with safe_test_file(test_file) as temp_path:
                # First run to get a BPM
                bpm1, error1 = self.analyzer.analyze_file(temp_path)
                if bpm1:
                    print(f"First analysis: {bpm1} BPM")
                    # Second run should read from tag
                    bpm2 = self.analyzer.get_bpm(temp_path)
                    print(f"Read from tag: {bpm2} BPM")
                    self.assertEqual(bpm1, bpm2)

    def test_bpm_ranges(self):
        """Test BPM detection across different tempo ranges"""
        results = {}
        
        for test_file in self.test_files:
            print(f"\nAnalyzing: {test_file.name}")
            with safe_test_file(test_file) as temp_path:
                bpm, error = self.analyzer.analyze_file(temp_path)
                if bpm:
                    results[test_file.name] = bpm
                    print(f"Detected BPM: {bpm}")
                    # Basic sanity checks
                    self.assertGreaterEqual(bpm, 30, "BPM too low")
                    self.assertLessEqual(bpm, 300, "BPM too high")
                else:
                    print(f"Error: {error}")
        
        # Print summary of detected ranges
        if results:
            print("\nBPM Range Summary:")
            print(f"Lowest: {min(results.values()):.1f} BPM")
            print(f"Highest: {max(results.values()):.1f} BPM")
            for name, bpm in sorted(results.items(), key=lambda x: x[1]):
                print(f"{name}: {bpm:.1f} BPM")

    def test_error_conditions(self):
        """Test various error conditions"""
        # Test non-existent file
        print("\nTesting non-existent file")
        bpm, error = self.analyzer.analyze_file(Path("nonexistent.mp3"))
        self.assertIsNone(bpm)
        self.assertEqual(error, "File not found")
        
        # Test with very short file
        print("\nTesting corrupted/short file")
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tf:
            temp_path = Path(tf.name)
            with open(tf.name, 'wb') as f:
                f.write(b'ID3' + b'\x00' * 100)  # Invalid/empty MP3
        try:
            bpm, error = self.analyzer.analyze_file(temp_path)
            self.assertIsNone(bpm)
            self.assertIsNotNone(error)
            print(f"Error (expected): {error}")
        finally:
            temp_path.unlink(missing_ok=True)
            
        # Test with file containing no audio content
        if self.test_files:
            print("\nTesting silent/empty audio")
            with safe_test_file(self.test_files[0]) as temp_path:
                # Create a valid MP3 structure but with zero amplitude
                audio_data, sample_rate = self.analyzer.read_mp3_data(str(temp_path))
                if audio_data is not None:
                    audio_data *= 0  # Zero out the audio
                    bpm = self.analyzer.detect_bpm(audio_data, sample_rate)
                    self.assertIsNone(bpm)

if __name__ == '__main__':
    unittest.main()
