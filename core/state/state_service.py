# core/state/state_service.py

from typing import Dict, Type, TypeVar, Optional, Generic
from pathlib import Path
import logging
import asyncio

from core.services.service_base import ServiceProvider
from .base_state import BaseState, StateError

T = TypeVar('T', bound=BaseState)

class StateService(ServiceProvider, Generic[T]):
    """Central manager for application state instances."""

    def __init__(self):
        super().__init__("state_service")  # Add name parameter
        self.logger = logging.getLogger('state_service')
        self._states: Dict[str, BaseState] = {}
        self._cache_dir = Path.home() / ".m3u_library_manager" / "state"
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize service."""
        if self._initialized:
            self.logger.warning("State service already initialized")
            return

        try:
            self.logger.info("Initializing state service")
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            self.logger.info("State service initialization complete")
        except Exception as e:
            self.logger.error(f"State service initialization failed: {e}")
            raise StateError(f"Service initialization failed: {str(e)}")

    async def start(self) -> None:
        """Start service - implement abstract method."""
        self.logger.debug("Starting state service")
        pass

    async def stop(self) -> None:
        """Stop service - implement abstract method."""
        self.logger.debug("Stopping state service")
        try:
            # Save all states before stopping
            self.save_all_states()
        except Exception as e:
            self.logger.error(f"Error saving states during stop: {e}")
            
    def register_state(self, state_id: str, state_class: Type[T], **kwargs) -> T:
        """
        Register a new state instance.

        Args:
            state_id: Unique identifier for the state
            state_class: State class to instantiate
            **kwargs: Additional arguments for state initialization

        Returns:
            Initialized state instance
        """
        if state_id in self._states:
            self.logger.warning(f"State already registered: {state_id}")
            return self._states[state_id]

        try:
            self.logger.debug(f"Registering new state: {state_id}")
            
            # Create state instance with cache directory
            state = state_class(cache_dir=self._cache_dir, **kwargs)
            self._states[state_id] = state

            # Initialize if service is already initialized
            if self._initialized:
                asyncio.create_task(self._initialize_state(state))

            return state

        except Exception as e:
            self.logger.error(f"Failed to register state {state_id}: {e}")
            raise StateError(f"State registration failed: {str(e)}")

    def get_state(self, state_id: str) -> Optional[BaseState]:
        """
        Get a registered state instance.

        Args:
            state_id: State identifier

        Returns:
            State instance if found, None otherwise
        """
        return self._states.get(state_id)

    def remove_state(self, state_id: str) -> None:
        """
        Remove a registered state.

        Args:
            state_id: State identifier to remove
        """
        if state_id in self._states:
            try:
                self.logger.debug(f"Removing state: {state_id}")
                state = self._states[state_id]
                state.cleanup()
                del self._states[state_id]
            except Exception as e:
                self.logger.error(f"Error removing state {state_id}: {e}")
                raise StateError(f"Failed to remove state: {str(e)}")

    async def _initialize_state(self, state: BaseState) -> None:
        """Initialize a single state instance."""
        try:
            await state.initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize state: {e}")
            raise StateError(f"State initialization failed: {str(e)}")



    def save_all_states(self) -> None:
        """Save all registered states to cache."""
        try:
            self.logger.info("Saving all states")
            for state_id, state in self._states.items():
                try:
                    state.save_state(state_id)
                except Exception as e:
                    self.logger.error(f"Failed to save state {state_id}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to save states: {e}")
            raise StateError(f"State save failed: {str(e)}")

    def load_all_states(self) -> None:
        """Load all registered states from cache."""
        try:
            self.logger.info("Loading all states")
            for state_id, state in self._states.items():
                try:
                    state.load_state(state_id)
                except Exception as e:
                    self.logger.error(f"Failed to load state {state_id}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load states: {e}")
            raise StateError(f"State load failed: {str(e)}")

    def cleanup(self) -> None:
        """Clean up all states and service resources."""
        try:
            self.logger.info("Cleaning up state service")
            
            # Clean up all states
            for state_id, state in list(self._states.items()):
                try:
                    state.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up state {state_id}: {e}")
                    
            self._states.clear()
            self._initialized = False
            
        except Exception as e:
            self.logger.error(f"State service cleanup failed: {e}")
            raise StateError(f"Service cleanup failed: {str(e)}")