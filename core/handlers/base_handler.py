# core/handlers/base_handler.py

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, Dict, Any
import logging

class BaseHandler(QObject):
    """Base class for all handlers with common functionality."""

    # Common signals
    error_occurred = pyqtSignal(str)  # For error reporting
    status_changed = pyqtSignal(str)  # For status updates
    progress_updated = pyqtSignal(int)  # For progress reporting (0-100)
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize base handler.
        
        Args:
            name: Optional name for the handler (used for logging)
        """
        super().__init__()
        self.name = name or self.__class__.__name__
        
        # Initialize logger
        self.logger = logging.getLogger(self.name)
        self._setup_logging()
        
        # State tracking
        self._initialized = False
        self._is_active = False
        
    def _setup_logging(self):
        """Set up logging for the handler."""
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.DEBUG)
            
    def report_error(self, error: str, log_level: int = logging.ERROR):
        """
        Report an error through both signals and logging.
        
        Args:
            error: Error message
            log_level: Logging level to use
        """
        self.logger.log(log_level, error)
        self.error_occurred.emit(error)
        
    def update_status(self, status: str):
        """
        Update handler status.
        
        Args:
            status: Status message
        """
        self.logger.debug(status)
        self.status_changed.emit(status)
        
    def update_progress(self, progress: int):
        """
        Update progress value.
        
        Args:
            progress: Progress value (0-100)
        """
        # Ensure valid range
        progress = max(0, min(100, progress))
        self.progress_updated.emit(progress)
        
    def initialize(self) -> bool:
        """
        Initialize the handler. Should be overridden by subclasses.
        
        Returns:
            bool: Success status
        """
        if self._initialized:
            self.logger.warning("Handler already initialized")
            return True
            
        try:
            self.update_status("Initializing handler...")
            success = self._do_initialize()
            
            if success:
                self._initialized = True
                self.update_status("Handler initialized")
            else:
                self.report_error("Handler initialization failed")
                
            return success
            
        except Exception as e:
            self.report_error(f"Error during initialization: {str(e)}")
            return False
            
    def _do_initialize(self) -> bool:
        """
        Perform actual initialization. Must be implemented by subclasses.
        
        Returns:
            bool: Success status
        """
        return True
        
    def start(self) -> bool:
        """
        Start the handler's operation.
        
        Returns:
            bool: Success status
        """
        if not self._initialized:
            self.report_error("Cannot start uninitialized handler")
            return False
            
        if self._is_active:
            self.logger.warning("Handler already active")
            return True
            
        try:
            self.update_status("Starting handler...")
            success = self._do_start()
            
            if success:
                self._is_active = True
                self.update_status("Handler started")
            else:
                self.report_error("Handler failed to start")
                
            return success
            
        except Exception as e:
            self.report_error(f"Error starting handler: {str(e)}")
            return False
            
    def _do_start(self) -> bool:
        """
        Perform actual start operation. Can be overridden by subclasses.
        
        Returns:
            bool: Success status
        """
        return True
        
    def stop(self) -> bool:
        """
        Stop the handler's operation.
        
        Returns:
            bool: Success status
        """
        if not self._is_active:
            return True
            
        try:
            self.update_status("Stopping handler...")
            success = self._do_stop()
            
            if success:
                self._is_active = False
                self.update_status("Handler stopped")
            else:
                self.report_error("Handler failed to stop")
                
            return success
            
        except Exception as e:
            self.report_error(f"Error stopping handler: {str(e)}")
            return False
            
    def _do_stop(self) -> bool:
        """
        Perform actual stop operation. Can be overridden by subclasses.
        
        Returns:
            bool: Success status
        """
        return True
        
    def cleanup(self):
        """Clean up handler resources."""
        try:
            self.logger.debug("Cleaning up handler resources")
            self.stop()
            self._do_cleanup()
            self._initialized = False
            self._is_active = False
            self.logger.debug("Cleanup complete")
            
        except Exception as e:
            self.report_error(f"Error during cleanup: {str(e)}")
            
    def _do_cleanup(self):
        """
        Perform actual cleanup. Can be overridden by subclasses.
        """
        pass
        
    @property
    def is_initialized(self) -> bool:
        """Check if handler is initialized."""
        return self._initialized
        
    @property
    def is_active(self) -> bool:
        """Check if handler is active."""
        return self._is_active