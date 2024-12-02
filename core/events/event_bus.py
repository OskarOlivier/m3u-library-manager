# core/events/event_bus.py

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, Dict, Any

@dataclass
class Event:
    """Simple event class."""
    type: str
    data: Optional[Dict[str, Any]] = None

# Common event types
class EventType:
    CACHE_READY = "cache_ready"
    CACHE_UPDATED = "cache_updated"
    RELATIONSHIPS_CHANGED = "relationships_changed"
    CONTEXT_INITIALIZED = "context_initialized"
    
class EventBus(QObject):
    """Central event bus using Qt signals."""
    
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
        """Emit an event."""
        event = Event(event_type, data)
        self.event_occurred.emit(event)

class RelationshipEvents:
    """Event definitions for relationship-related events."""
    
    relationship_updated = pyqtSignal(Path, float)  # playlist, strength
    relationship_cleared = pyqtSignal(Path)  # playlist