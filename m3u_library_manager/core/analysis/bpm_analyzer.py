from pathlib import Path
from typing import Optional, Tuple, Dict
import os
import shutil
import tempfile
import numpy as np
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import logging

class BPMAnalyzer:
    """Analyzes and updates BPM metadata for MP3 files"""
    
    @staticmethod
    def read_mp3_data(file_path: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Read MP3 file using mutagen and convert to numpy array
        """
        try:
            audio = MP3(file_path)
            sample_rate = audio.info.sample_rate
            
            # Read the file in chunks to handle alignment
            chunk_size = 2048  # Must be even
            chunks = []
            
            with open(file_path, 'rb') as f:
                # Skip ID3 tags if present
                if f.read(3) == b'ID3':
                    f.seek(6)
                    size = 0
                    for i in range(4):
                        size = (size << 7) | (f.read(1)[0] & 0x7F)
                    f.seek(10 + size)
                else:
                    f.seek(0)
                
                # Read data in aligned chunks
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    # Ensure chunk length is even
                    if len(chunk) % 2 != 0:
                        chunk = chunk[:-1]
                    if chunk:
                        chunks.append(np.frombuffer(chunk, dtype=np.int16))
            
            if not chunks:
                raise ValueError("No audio data read")
                
            # Combine chunks and convert to float
            audio_data = np.concatenate(chunks)
            audio_data = audio_data.astype(np.float32) / 32768.0
            
            return audio_data, sample_rate
                
        except Exception as e:
            logging.error(f"Error reading MP3: {e}")
            return None, None

    @staticmethod
    def detect_bpm(audio_data: np.ndarray, sample_rate: int) -> Optional[float]:
        """
        Detect BPM using tempo estimation
        Returns None if no clear tempo is found
        """
        try:
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Normalize
            audio_data = audio_data / np.max(np.abs(audio_data))

            # Parameters
            hop_length = 512
            win_length = 2048

            # Compute onset strength
            onset_env = np.zeros(len(audio_data) // hop_length)
            for i in range(len(onset_env)):
                start = i * hop_length
                end = start + win_length
                if end > len(audio_data):
                    break
                # Compute spectral flux
                window = audio_data[start:end] * np.hanning(win_length)
                mag = np.abs(np.fft.rfft(window))
                if i > 0:
                    # Difference between consecutive windows
                    onset_env[i] = np.sum(np.maximum(0, mag - prev_mag))
                prev_mag = mag

            # Find tempo through autocorrelation
            ac = np.correlate(onset_env, onset_env, mode='full')
            ac = ac[len(ac)//2:]  # Keep only positive lags

            # Convert lags to BPM
            lags = np.arange(len(ac))
            bpms = 60 * sample_rate / (hop_length * lags[1:])  # Convert lags to BPM

            # Find peaks in valid BPM range
            valid_bpms = []
            valid_strengths = []
            
            for i in range(1, len(ac)-1):
                bpm = 60 * sample_rate / (hop_length * i)
                if 30 <= bpm <= 300:  # Valid BPM range
                    if ac[i] > ac[i-1] and ac[i] > ac[i+1]:  # Peak
                        valid_bpms.append(bpm)
                        valid_strengths.append(ac[i])

            if not valid_bpms:
                return None

            # Return the strongest BPM
            strongest_idx = np.argmax(valid_strengths)
            return round(valid_bpms[strongest_idx], 1)

        except Exception as e:
            logging.error(f"BPM detection error: {e}")
            return None

    def analyze_file(self, file_path: Path) -> Tuple[Optional[float], Optional[str]]:
        """
        Analyze BPM of a single file and update its ID3 tag.
        Uses temporary file for safety.
        """
        temp_file = None
        try:
            if not file_path.exists():
                return None, "File not found"

            # Create temporary working copy
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tf:
                temp_file = tf.name
                shutil.copy2(str(file_path), temp_file)

            # Try to get original tags
            try:
                audio = EasyID3(str(file_path))
                original_tags = dict(audio)
            except Exception as e:
                return None, f"Failed to read ID3 tags: {e}"

            # Read and analyze audio
            audio_data, sample_rate = self.read_mp3_data(temp_file)
            if audio_data is None or sample_rate is None:
                return None, "Failed to read audio data"

            if len(audio_data) < sample_rate * 2:
                return None, "Audio file too short"
                
            if np.all(np.abs(audio_data) < 0.001):
                return None, "No audio content detected"

            # Detect BPM
            bpm = self.detect_bpm(audio_data, sample_rate)
            if bpm is None:
                return None, "No reliable tempo detected"

            # Update ID3 tag with safety check
            try:
                audio = EasyID3(str(file_path))
                audio['bpm'] = str(bpm)
                audio.save()
                
                # Verify the write
                audio = EasyID3(str(file_path))
                if 'bpm' not in audio or float(audio['bpm'][0]) != bpm:
                    raise ValueError("BPM tag verification failed")
                
                return bpm, None
                
            except Exception as e:
                # Restore original tags if write failed
                try:
                    audio = EasyID3(str(file_path))
                    for key in audio.keys():
                        del audio[key]
                    for key, value in original_tags.items():
                        audio[key] = value
                    audio.save()
                except:
                    pass
                return bpm, f"Failed to update BPM tag: {e}"

        except Exception as e:
            logging.error(f"Error analyzing {file_path}: {e}")
            return None, str(e)
            
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass

    def get_bpm(self, file_path: Path) -> Optional[float]:
        """
        Get BPM from ID3 tag if available, otherwise analyze file
        """
        try:
            # Try to read existing BPM tag
            audio = EasyID3(str(file_path))
            if 'bpm' in audio:
                try:
                    return float(audio['bpm'][0])
                except (ValueError, IndexError):
                    pass
                
            # If no tag or invalid, analyze file
            bpm, error = self.analyze_file(file_path)
            return bpm
            
        except Exception as e:
            logging.error(f"Error getting BPM for {file_path}: {e}")
            return None
