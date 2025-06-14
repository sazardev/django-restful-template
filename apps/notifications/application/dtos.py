"""
Notification Application DTOs.
DTOs para la aplicación de notificaciones.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from apps.notifications.domain.entities import NotificationType, NotificationPriority


@dataclass
class CreateNotificationDTO:
    """DTO para crear notificación."""
    
    user_id: UUID
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = None
    expires_in_hours: Optional[int] = None
    created_by_id: Optional[UUID] = None
    send_realtime: bool = True


@dataclass
class NotificationResponseDTO:
    """DTO de respuesta para notificación."""
    
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    priority: int
    data: Dict[str, Any]
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    @classmethod
    def from_entity(cls, entity) -> 'NotificationResponseDTO':
        """Crear DTO desde entidad."""
        return cls(
            id=str(entity.id),
            user_id=str(entity.user_id),
            title=entity.title,
            message=entity.message,
            notification_type=entity.notification_type.value,
            priority=entity.priority.value,
            data=entity.data or {},
            is_read=entity.is_read,
            created_at=entity.created_at,
            read_at=entity.read_at,
            expires_at=entity.expires_at
        )


@dataclass
class NotificationListDTO:
    """DTO para lista de notificaciones."""
    
    notifications: List[NotificationResponseDTO]
    total_count: int
    unread_count: int
    has_next: bool
    has_previous: bool


@dataclass
class NotificationFilterDTO:
    """DTO para filtros de notificación."""
    
    unread_only: bool = False
    notification_type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 20
    offset: int = 0


@dataclass
class MarkNotificationsDTO:
    """DTO para marcar notificaciones."""
    
    notification_ids: List[UUID]
    mark_as_read: bool = True


@dataclass
class BroadcastNotificationDTO:
    """DTO para broadcast de notificación."""
    
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = None
    target_all_users: bool = True
    target_groups: Optional[List[str]] = None
    target_user_ids: Optional[List[UUID]] = None
    expires_in_hours: Optional[int] = None


@dataclass
class NotificationStatsDTO:
    """DTO para estadísticas de notificaciones."""
    
    total_notifications: int
    unread_count: int
    read_count: int
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int]
    recent_notifications_count: int  # últimas 24 horas


@dataclass
class WebSocketMessageDTO:
    """DTO para mensajes WebSocket."""
    
    type: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'type': self.type,
            **self.data
        }


@dataclass
class NotificationChannelDTO:
    """DTO para canal de notificación."""
    
    id: str
    user_id: str
    channel_type: str
    channel_identifier: str
    is_active: bool
    is_verified: bool
    settings: Dict[str, Any]
    created_at: datetime
    last_used_at: Optional[datetime] = None


@dataclass
class CreateChannelDTO:
    """DTO para crear canal de notificación."""
    
    user_id: UUID
    channel_type: str
    channel_identifier: str
    settings: Optional[Dict[str, Any]] = None


@dataclass
class NotificationTemplateDTO:
    """DTO para plantilla de notificación."""
    
    id: str
    name: str
    description: str
    notification_type: str
    title_template: str
    message_template: str
    default_priority: int
    default_channels: List[str]
    is_active: bool


@dataclass
class CreateTemplateDTO:
    """DTO para crear plantilla de notificación."""
    
    name: str
    description: str
    notification_type: NotificationType
    title_template: str
    message_template: str
    default_priority: NotificationPriority = NotificationPriority.NORMAL
    default_channels: Optional[List[str]] = None


@dataclass
class NotificationFromTemplateDTO:
    """DTO para crear notificación desde plantilla."""
    
    template_name: str
    user_id: UUID
    context: Dict[str, Any]
    override_title: Optional[str] = None
    override_message: Optional[str] = None
    override_priority: Optional[NotificationPriority] = None
    created_by_id: Optional[UUID] = None


@dataclass
class AuctionNotificationDTO:
    """DTO para notificaciones de subasta."""
    
    auction_id: UUID
    auction_title: str
    vehicle_info: Dict[str, Any]
    notification_type: str  # 'created', 'bid', 'won', 'lost', 'ended'
    data: Optional[Dict[str, Any]] = None


@dataclass
class BidNotificationDTO:
    """DTO para notificaciones de puja."""
    
    auction_id: UUID
    bidder_id: UUID
    previous_bidder_id: Optional[UUID]
    bid_amount: float
    previous_amount: Optional[float] = None
