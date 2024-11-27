# gui/workers/async_base.py

from PyQt6.QtCore import QThread, pyqtSignal, QCoreApplication, QObject
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
            if self.progress_callback:
                self.progress.connect(self.progress_callback)
            
            # Run the coroutine and process Qt events periodically
            future = asyncio.ensure_future(self.coro)
            
            while not future.done() and self._is_running:
                loop.stop()
                loop.run_forever()
                QCoreApplication.processEvents()
                
            if not self._is_running:
                return
                
            result = future.result()
            
            if self._is_running:
                self.finished.emit(result)
                
        except Exception as e:
            if self._is_running:
                self.logger.error(f"Error in async operation: {e}", exc_info=True)
                self.error.emit(str(e))
                
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
            except Exception as e:
                self.logger.error(f"Error closing event loop: {e}")
            self._is_running = False
            
    def stop(self):
        """Safely stop the worker."""
        self._is_running = False
        
        try:
            if self.progress_callback:
                self.progress.disconnect()
            self.finished.disconnect()
            self.error.disconnect()
        except:
            pass
            
        self.wait()

class AsyncOperation(QObject):
    """Base class for async operations with proper cleanup."""
    
    def __init__(self):
        super().__init__()
        self.current_worker: Optional[AsyncWorker] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _start_operation(self, coro, progress_callback=None, 
                        on_finished=None, on_error=None):
        """Start an async operation with proper cleanup."""
        self._cleanup_current_worker()
        
        worker = AsyncWorker(coro, progress_callback)
        
        # Connect signals
        if on_finished:
            worker.finished.connect(on_finished)
        if on_error:
            worker.error.connect(on_error)
            
        # Always connect cleanup
        worker.finished.connect(lambda _: self._cleanup_worker(worker))
        worker.error.connect(lambda _: self._cleanup_worker(worker))
        
        self.current_worker = worker
        worker.start()
        
        return worker
        
    def _cleanup_current_worker(self):
        """Clean up the current worker if it exists."""
        if self.current_worker:
            try:
                self.current_worker.stop()
                self.current_worker = None
            except Exception as e:
                self.logger.error(f"Error cleaning up worker: {e}")
                
    def _cleanup_worker(self, worker: AsyncWorker):
        """Clean up a specific worker."""
        if worker == self.current_worker:
            worker.stop()
            self.current_worker = None
        
    def cleanup(self):
        """Clean up any running operations."""
        self._cleanup_current_worker()

class AsyncHelper(QThread):
    """Helper class to run coroutines from UI code."""

    finished = pyqtSignal(object)  # Signal for operation completion
    error = pyqtSignal(str)       # Signal for error reporting

    def __init__(self, coro, callback=None):
        super().__init__()
        self.coro = coro
        self.callback = callback
        self._is_running = False
        self.logger = logging.getLogger('async_helper')
        
        # Connect signals
        if callback:
            self.finished.connect(callback)

    def run(self):
        """Execute the coroutine in a new event loop."""
        self._is_running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self.logger.debug("Starting coroutine execution")
            result = loop.run_until_complete(self.coro)
            if self._is_running and self.callback:
                self.finished.emit(result)
        except Exception as e:
            self.logger.error(f"Error executing coroutine: {e}", exc_info=True)
            if self._is_running:
                self.error.emit(str(e))
        finally:
            self.logger.debug("Closing event loop")
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
            except Exception as e:
                self.logger.error(f"Error closing event loop: {e}")
            self._is_running = False

    def stop(self):
        """Safely stop the thread."""
        self._is_running = False
        if self.callback:
            try:
                self.finished.disconnect()
            except:
                pass
        try:
            self.error.disconnect()
        except:
            pass
        self.wait()

    def start(self):
        """Start the thread and store reference for cleanup."""
        super().start()
        return self
        
    def __del__(self):
        """Ensure thread is stopped on deletion."""
        self.stop()