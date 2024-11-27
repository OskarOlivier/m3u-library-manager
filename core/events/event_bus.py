# core/events/event_bus.py
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any, Optional
from pathlib import Path

class EventType:
    """Enumeration of event types."""
    CACHE_READY = "cache_ready"
    CACHE_UPDATED = "cache_updated"
    RELATIONSHIPS_CHANGED = "relationships_changed"
    # Add more event types as needed

class Event:
    """Base event class."""
    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        self.type = event_type
        self.data = data or {}

class EventBus(QObject):
    """Central event bus for application-wide events."""
    
    event_occurred = pyqtSignal(Event)
    
    _instance = None
    
    def __init__(self):
        if EventBus._instance is not None:
            raise RuntimeError("EventBus is a singleton")
        super().__init__()
        
    @classmethod
    def get_instance(cls) -> 'EventBus':
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance
        
    def emit_event(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """Emit an event with optional data."""
        event = Event(event_type, data)
        self.event_occurred.emit(event)

class RelationshipEvents:
    """Event definitions for relationship-related events."""
    
    relationship_updated = pyqtSignal(Path, float)  # playlist, strength
    relationship_cleared = pyqtSignal(Path)  # playlist