"""
Simple Notification Entity for current implementation.
Entidad simple de notificación para la implementación actual.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from apps.notifications.domain.entities import NotificationType, NotificationPriority


@dataclass
class SimpleNotificationEntity:
    """Entidad simple de notificación."""
    
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    data: Dict[str, Any]
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def mark_as_read(self) -> None:
        """Marcar notificación como leída."""
        self.is_read = True
        self.read_at = datetime.now()
    
    def is_expired(self) -> bool:
        """Verificar si la notificación ha expirado."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para WebSocket."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'title': self.title,
            'message': self.message,
            'type': self.notification_type.value,
            'priority': self.priority.value,
            'data': self.data or {},
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }
