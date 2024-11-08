# gui/windows/pages/curation/handlers/stats_handler.py
from PyQt6.QtCore import QObject, QTimer
from pathlib import Path
import logging
from typing import Optional

from utils.playlist.stats import calculate_playlist_stats

class StatsHandler(QObject):
    """Handles playlist statistics calculation."""
    
    def __init__(self, state, playlists_dir: Path):
        super().__init__()
        self.state = state
        self.playlists_dir = playlists_dir
        self.is_running = False
        self.logger = logging.getLogger('stats_handler')

    def start_analysis(self):
        """Start playlist analysis."""
        if self.is_running:
            return

        self.is_running = True
        self.state.set_status("Calculating playlist statistics...")
        
        try:
            def progress_callback(value: int):
                if self.is_running:  # Only update if still running
                    self.state.update_progress(value)

            # Calculate stats with progress updates
            total, unplaylisted = calculate_playlist_stats(
                self.playlists_dir,
                progress_callback
            )

            if self.is_running:  # Only update if not stopped
                self.state.update_stats(total, unplaylisted)
                self.state.set_status("Stats calculation complete")
                self.state.update_progress(100)

                # Hide progress after a delay
                QTimer.singleShot(1000, lambda: self.state.update_progress(0))

        except Exception as e:
            self.logger.error(f"Stats calculation failed: {e}")
            if self.is_running:
                self.state.report_error(f"Failed to calculate stats: {str(e)}")
        finally:
            self.is_running = False

    def stop_analysis(self):
        """Stop current analysis."""
        if self.is_running:
            self.logger.info("Stopping stats calculation")
            self.is_running = False