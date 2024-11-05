# workers/sync_workers.py

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from pathlib import Path
import asyncio
from typing import Set, Optional, Dict, Any
import logging

from core.sync.file_comparator import FileComparator, ComparisonResult
from core.sync.sync_operations import SyncOperations

class WorkerBase(QThread):
    """Base class for background workers with proper cleanup."""
    
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_running = False
        self._loop = None
        
    def run(self):
        """Template method for worker execution."""
        self._is_running = True
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self.logger.debug("Starting worker execution")
            result = self._loop.run_until_complete(self._execute())
            
            if self._is_running:
                self._emit_result(result)
                
        except Exception as e:
            if self._is_running:
                self.logger.error(f"Worker error: {e}", exc_info=True)
                self.error.emit(str(e))
                
        finally:
            self.cleanup()
            
    async def _execute(self):
        """Override this method to implement worker logic."""
        raise NotImplementedError
        
    def _emit_result(self, result):
        """Override this method to emit the appropriate result signal."""
        raise NotImplementedError
        
    def cleanup(self):
        """Clean up resources."""
        self._is_running = False
        
        if self._loop:
            try:
                self.logger.debug("Cleaning up event loop")
                self._loop.run_until_complete(self._loop.shutdown_asyncgens())
                self._loop.close()
            except Exception as e:
                self.logger.error(f"Error closing event loop: {e}")
                
        self._loop = None
        self.logger.debug("Worker cleanup complete")
        
    def stop(self):
        """Stop the worker safely."""
        self.logger.debug("Stopping worker")
        self._is_running = False
        self.wait()

class ComparisonWorker(WorkerBase):
    """Worker for playlist file comparison."""
    
    finished = pyqtSignal(object)  # ComparisonResult
    
    def __init__(self, comparator: FileComparator, playlist_path: Path,
                 local_base: Path, remote_base: str):
        super().__init__()
        self.comparator = comparator
        self.playlist_path = playlist_path
        self.local_base = local_base
        self.remote_base = remote_base
        
    async def _execute(self):
        """Run comparison operation."""
        self.logger.info(f"Starting comparison for {self.playlist_path.name}")
        
        result = await self.comparator.compare_locations(
            self.playlist_path,
            self.local_base,
            self.remote_base,
            lambda p: self.progress.emit(int(p))
        )
        
        self.logger.info("Comparison complete")
        return result
        
    def _emit_result(self, result: ComparisonResult):
        """Emit comparison results."""
        self.finished.emit(result)

class SyncWorker(WorkerBase):
    """Worker for playlist synchronization."""
    
    finished = pyqtSignal()
    
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
        
    async def _execute(self):
        """Run sync operation."""
        self.logger.info(f"Starting sync for {self.playlist_path.name}")
        
        await self.sync_ops.sync_playlist(
            playlist_path=self.playlist_path,
            add_to_remote=self.add_remote,
            add_to_local=self.add_local,
            remove_from_remote=self.remove_remote,
            remove_from_local=self.remove_local,
            progress_callback=lambda p: self.progress.emit(int(p))
        )
        
        self.logger.info("Sync complete")
        
    def _emit_result(self, _):
        """Emit completion signal."""
        self.finished.emit()