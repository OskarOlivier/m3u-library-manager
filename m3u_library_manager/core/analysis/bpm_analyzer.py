# core/analysis/bpm_analyzer.py
from utils.id3.reader import get_bpm_tag, get_id3_tags
from utils.id3.writer import set_bpm_tag

class BPMAnalyzer:
    # Existing methods ...

    def analyze_file(self, file_path: Path) -> Tuple[Optional[float], Optional[str]]:
        """
        Analyze BPM of a single file and update its ID3 tag.
        """
        try:
            # Use get_id3_tags to retrieve tags
            original_tags = get_id3_tags(str(file_path))
            if original_tags is None:
                return None, "Failed to read ID3 tags"
            
            # Read and analyze audio data, detect BPM, etc.
            # ...

            # Use set_bpm_tag to write the BPM to the file
            if bpm is not None:
                if not set_bpm_tag(str(file_path), bpm):
                    return bpm, "Failed to update BPM tag"
                return bpm, None

        except Exception as e:
            logging.error(f"Error analyzing {file_path}: {e}")
            return None, str(e)

