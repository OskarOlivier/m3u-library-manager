# gui/workers/sync_workers.py
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
import asyncio
from typing import Set

from core.sync.file_comparator import FileComparator, ComparisonResult
from core.sync.sync_operations import SyncOperations

class ComparisonWorker(QThread):
    """Background worker for file comparison"""
    finished = pyqtSignal(ComparisonResult)
    progress = pyqtSignal(float)
    error = pyqtSignal(str)
    
    def __init__(self, comparator: FileComparator, playlist_path: Path,
                 local_base: Path, remote_base: str):
        super().__init__()
        self.comparator = comparator
        self.playlist_path = playlist_path
        self.local_base = local_base
        self.remote_base = remote_base
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.comparator.compare_locations(
                    self.playlist_path,
                    self.local_base,
                    self.remote_base,
                    lambda p: self.progress.emit(p)
                )
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class SyncWorker(QThread):
    """Background worker for sync operations"""
    finished = pyqtSignal()
    progress = pyqtSignal(float)
    error = pyqtSignal(str)
    
    def __init__(self, sync_ops: SyncOperations, playlist_path: Path,
                 add_remote: Set[Path], add_local: Set[Path],
                 remove_remote: Set[Path], remove_local: Set[Path]):
        super().__init__()
        self.sync_ops = sync_ops
        self.playlist_path = playlist_path
        self.add_remote = add_remote
        self.add_local = add_local
        self.remove_remote = remove_remote
        self.remove_local = remove_local
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.sync_ops.sync_playlist(
                    self.playlist_path,
                    self.add_remote,
                    self.add_local,
                    self.remove_remote,
                    self.remove_local,
                    lambda p: self.progress.emit(p)
                )
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))