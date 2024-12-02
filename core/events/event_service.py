# core/events/event_service.py

from core.events.event_bus import Event
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Callable, Optional
import logging

class EventService(QObject):
    """Service for handling application events."""
    
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.name = "event_service"
        self.logger = logging.getLogger('event_service')
        self._handlers: Dict[str, set[Callable]] = {}

    async def initialize(self) -> None:
        """Initialize the event service."""
        self.logger.debug("Initializing event service")
        pass

    async def start(self) -> None:
        """Start the event service."""
        self.logger.debug("Starting event service")
        pass

    async def stop(self) -> None:
        """Stop the event service."""
        self.logger.debug("Stopping event service")
        self.cleanup()
        
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to events of a specific type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Remove a subscription."""
        if event_type in self._handlers:
            self._handlers[event_type].discard(callback)

    def emit_event(self, event_type: str, data: Optional[dict] = None) -> None:
        """Emit an event to all subscribers."""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")
                    self.error_occurred.emit(str(e))

    def cleanup(self) -> None:
        """Clean up service resources."""
        self._handlers.clear()