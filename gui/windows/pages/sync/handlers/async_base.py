# gui/windows/pages/sync/handlers/async_base.py

from PyQt6.QtCore import QThread, pyqtSignal, QObject, QCoreApplication
import asyncio
import logging
from typing import Any, Callable, Optional

class AsyncWorker(QThread):
    """Base worker for handling async operations safely."""
    
    finished = pyqtSignal(object)  # Emits result when done
    error = pyqtSignal(str)  # Emits error message if failed
    progress = pyqtSignal(int)  # Emits progress updates
    
    def __init__(self, coro, progress_callback: Optional[Callable[[int], None]] = None):
        super().__init__()
        self.coro = coro
        self.progress_callback = progress_callback
        self._is_running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
    def run(self):
        """Execute the coroutine in a new event loop."""
        self._is_running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            self.logger.debug("Starting async operation")
            if self.progress_callback:
                self.progress.connect(self.progress_callback)
            
            # Run the coroutine and process Qt events periodically
            self.logger.debug("Creating future")
            future = asyncio.ensure_future(self.coro)
            
            while not future.done() and self._is_running:
                self.logger.debug("Processing events")
                loop.stop()
                loop.run_forever()
                QCoreApplication.processEvents()
                
            if not self._is_running:
                self.logger.debug("Operation was cancelled")
                return
                
            self.logger.debug("Getting operation result")
            result = future.result()
            
            if self._is_running:
                self.logger.debug("Emitting finished signal")
                self.finished.emit(result)
                
        except Exception as e:
            if self._is_running:
                self.logger.error(f"Error in async operation: {e}", exc_info=True)
                self.error.emit(str(e))
                
        finally:
            try:
                self.logger.debug("Cleaning up event loop")
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
            except Exception as e:
                self.logger.error(f"Error closing event loop: {e}")
            self._is_running = False
            self.logger.debug("Async operation complete")
            
    def stop(self):
        """Safely stop the worker."""
        self.logger.debug("Stopping worker")
        self._is_running = False
        
        try:
            self.logger.debug("Disconnecting signals")
            if self.progress_callback:
                self.progress.disconnect()
            self.finished.disconnect()
            self.error.disconnect()
        except Exception as e:
            self.logger.error(f"Error disconnecting signals: {e}")
            
        self.logger.debug("Waiting for thread to finish")
        self.wait()
        self.logger.debug("Worker stopped")

class AsyncOperation(QObject):
    """Base class for async operations with proper cleanup."""
    
    def __init__(self):
        super().__init__()
        self.current_worker: Optional[AsyncWorker] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
    def _start_operation(self, coro, progress_callback=None, 
                        on_finished=None, on_error=None):
        """Start an async operation with proper cleanup."""
        self.logger.debug("Starting new operation")
        self._cleanup_current_worker()
        
        worker = AsyncWorker(coro, progress_callback)
        
        # Connect signals
        if on_finished:
            self.logger.debug("Connecting finished callback")
            worker.finished.connect(on_finished)
        if on_error:
            self.logger.debug("Connecting error callback")
            worker.error.connect(on_error)
            
        # Always connect cleanup
        worker.finished.connect(lambda _: self._cleanup_worker(worker))
        worker.error.connect(lambda _: self._cleanup_worker(worker))
        
        self.current_worker = worker
        self.logger.debug("Starting worker thread")
        worker.start()
        
        return worker
        
    def _cleanup_current_worker(self):
        """Clean up the current worker if it exists."""
        if self.current_worker:
            self.logger.debug("Cleaning up current worker")
            try:
                self.current_worker.stop()
                self.current_worker = None
            except Exception as e:
                self.logger.error(f"Error cleaning up worker: {e}")
                
    def _cleanup_worker(self, worker: AsyncWorker):
        """Clean up a specific worker."""
        if worker == self.current_worker:
            self.logger.debug("Cleaning up worker")
            worker.stop()
            self.current_worker = None
        
    def cleanup(self):
        """Clean up any running operations."""
        self.logger.debug("Cleaning up all operations")
        self._cleanup_current_worker()