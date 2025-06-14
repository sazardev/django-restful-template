"""
Event Bus Implementation
Simple event bus for domain events
"""

from typing import Dict, List, Callable, Any
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """Simple event bus implementation for handling domain events"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def register(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event_type: str, event_data: Any):
        """Publish an event"""
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {e}")
    
    def unregister(self, event_type: str, handler: Callable):
        """Unregister an event handler"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass


# Global event bus instance
event_bus = EventBus()
