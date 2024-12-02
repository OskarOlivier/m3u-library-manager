# core/state/base_state.py

from typing import Dict, Any, Optional, TypeVar, Generic
from PyQt6.QtCore import QObject, pyqtSignal
import logging
import json
from pathlib import Path
import asyncio

T = TypeVar('T')

class StateError(Exception):
    """Custom exception for state-related errors."""
    pass

class BaseState(QObject, Generic[T]):
    """Base class for application state management."""

    # Core signals
    status_changed = pyqtSignal(str)  # Status message updates
    error_occurred = pyqtSignal(str)  # Error notifications
    progress_updated = pyqtSignal(int)  # Progress updates (0-100)
    state_changed = pyqtSignal(object)  # Generic state change notification
    
    # Lifecycle signals
    initialized = pyqtSignal()  # State initialization complete
    reset = pyqtSignal()  # State reset complete
    saved = pyqtSignal(str)  # State saved (cache_key)
    loaded = pyqtSignal(str)  # State loaded (cache_key)

    def __init__(self, cache_dir: Optional[Path] = None):
        super().__init__()
        
        # Initialize core attributes
        self._initialized = False
        self._is_busy = False
        self._cache_dir = cache_dir or Path.home() / ".m3u_library_manager" / "state"
        
        # Set up logging
        self.logger = logging.getLogger(f'state.{self.__class__.__name__.lower()}')
        self.logger.setLevel(logging.DEBUG)

        # Ensure cache directory exists
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_initialized(self) -> bool:
        """Check if state is initialized."""
        return self._initialized

    @property
    def is_busy(self) -> bool:
        """Check if state is currently processing an operation."""
        return self._is_busy

    def set_status(self, message: str) -> None:
        """Update status message."""
        self.logger.debug(f"Status: {message}")
        self.status_changed.emit(message)

    def report_error(self, error: str) -> None:
        """Report an error condition."""
        self.logger.error(f"Error: {error}")
        self.error_occurred.emit(error)
        self.set_status(f"Error: {error}")

    def update_progress(self, value: int) -> None:
        """Update progress value (0-100)."""
        self.progress_updated.emit(max(0, min(100, value)))

    async def initialize(self) -> None:
        """Initialize state asynchronously."""
        if self._initialized:
            self.logger.warning("State already initialized")
            return

        try:
            self._is_busy = True
            self.set_status("Initializing state...")
            
            await self._do_initialize()
            
            self._initialized = True
            self.initialized.emit()
            self.set_status("State initialized")

        except Exception as e:
            self.report_error(f"Initialization failed: {str(e)}")
            raise StateError(f"Failed to initialize state: {str(e)}")
        finally:
            self._is_busy = False

    async def _do_initialize(self) -> None:
        """Override to implement actual initialization logic."""
        pass

    def reset_state(self) -> None:
        """Reset state to initial values."""
        try:
            self._is_busy = True
            self.set_status("Resetting state...")
            
            self._do_reset()
            
            self.reset.emit()
            self.set_status("State reset complete")

        except Exception as e:
            self.report_error(f"Reset failed: {str(e)}")
            raise StateError(f"Failed to reset state: {str(e)}")
        finally:
            self._is_busy = False

    def _do_reset(self) -> None:
        """Override to implement actual reset logic."""
        pass

    def save_state(self, cache_key: str) -> None:
        """Save current state to cache."""
        if not self._cache_dir:
            return

        try:
            self._is_busy = True
            self.set_status("Saving state...")

            # Get serializable state
            state_data = self._get_serializable_state()
            
            # Save to cache file
            cache_file = self._cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2)

            self.saved.emit(cache_key)
            self.set_status("State saved")

        except Exception as e:
            self.report_error(f"Save failed: {str(e)}")
            raise StateError(f"Failed to save state: {str(e)}")
        finally:
            self._is_busy = False

    def load_state(self, cache_key: str) -> bool:
        """Load state from cache."""
        if not self._cache_dir:
            return False

        try:
            self._is_busy = True
            self.set_status("Loading state...")

            # Load from cache file
            cache_file = self._cache_dir / f"{cache_key}.json"
            if not cache_file.exists():
                self.logger.debug(f"No cached state found for key: {cache_key}")
                return False

            with open(cache_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # Restore state
            self._restore_from_state(state_data)

            self.loaded.emit(cache_key)
            self.set_status("State loaded")
            return True

        except Exception as e:
            self.report_error(f"Load failed: {str(e)}")
            raise StateError(f"Failed to load state: {str(e)}")
        finally:
            self._is_busy = False

    def _get_serializable_state(self) -> Dict[str, Any]:
        """Override to implement state serialization."""
        return {}

    def _restore_from_state(self, state_data: Dict[str, Any]) -> None:
        """Override to implement state restoration."""
        pass

    def cleanup(self) -> None:
        """Clean up state resources."""
        try:
            self._is_busy = True
            self.set_status("Cleaning up...")
            
            self._do_cleanup()
            
            self.set_status("Cleanup complete")

        except Exception as e:
            self.report_error(f"Cleanup failed: {str(e)}")
            raise StateError(f"Failed to clean up state: {str(e)}")
        finally:
            self._is_busy = False
            self._initialized = False

    def _do_cleanup(self) -> None:
        """Override to implement actual cleanup logic."""
        pass