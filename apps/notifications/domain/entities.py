"""
Notification Domain Entities.
Entidades de dominio para el sistema de notificaciones.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID


class NotificationType(Enum):
    """Tipos de notificación."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    URGENT = "urgent"


class NotificationChannel(Enum):
    """Canales de notificación."""
    WEB = "web"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBSOCKET = "websocket"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationStatus(Enum):
    """Estados de notificación."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


class NotificationPriority(Enum):
    """Prioridades de notificación."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class NotificationTemplate:
    """Plantilla de notificación - Value Object."""
    subject_template: str
    body_template: str
    html_template: Optional[str] = None
    variables: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
    
    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Renderizar plantilla con contexto."""
        subject = self.subject_template.format(**context)
        body = self.body_template.format(**context)
        
        rendered = {
            'subject': subject,
            'body': body
        }
        
        if self.html_template:
            rendered['html'] = self.html_template.format(**context)
        
        return rendered


@dataclass
class NotificationDelivery:
    """Entrega de notificación por canal."""
    id: UUID
    notification_id: UUID
    channel: NotificationChannel
    recipient: str
    status: NotificationStatus
    attempts: int
    last_attempt_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def mark_as_sent(self) -> None:
        """Marcar como enviada."""
        self.status = NotificationStatus.SENT
        self.last_attempt_at = datetime.now()
    
    def mark_as_delivered(self) -> None:
        """Marcar como entregada."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_as_read(self) -> None:
        """Marcar como leída."""
        self.status = NotificationStatus.READ
        self.read_at = datetime.now()
    
    def mark_as_failed(self, error: str) -> None:
        """Marcar como fallida."""
        self.status = NotificationStatus.FAILED
        self.error_message = error
        self.last_attempt_at = datetime.now()
        self.attempts += 1


@dataclass
class NotificationEntity:
    """Entidad principal de notificación."""
    id: UUID
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    sender_id: Optional[UUID]
    recipient_id: UUID
    recipient_group_id: Optional[UUID]
    channels: List[NotificationChannel]
    template: Optional[NotificationTemplate]
    context_data: Dict[str, Any]
    scheduled_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    deliveries: List[NotificationDelivery] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.deliveries is None:
            self.deliveries = []
        if self.tags is None:
            self.tags = []
        if self.context_data is None:
            self.context_data = {}
    
    def is_scheduled(self) -> bool:
        """Verificar si está programada."""
        return self.scheduled_at is not None and self.scheduled_at > datetime.now()
    
    def is_expired(self) -> bool:
        """Verificar si ha expirado."""
        return self.expires_at is not None and self.expires_at < datetime.now()
    
    def should_be_sent(self) -> bool:
        """Verificar si debe ser enviada."""
        if self.is_expired():
            return False
        
        if self.is_scheduled():
            return False
        
        # Verificar si ya fue enviada a todos los canales
        for channel in self.channels:
            channel_delivery = self.get_delivery_for_channel(channel)
            if not channel_delivery or channel_delivery.status == NotificationStatus.PENDING:
                return True
        
        return False
    
    def get_delivery_for_channel(self, channel: NotificationChannel) -> Optional[NotificationDelivery]:
        """Obtener entrega para un canal específico."""
        for delivery in self.deliveries:
            if delivery.channel == channel:
                return delivery
        return None
    
    def add_delivery(self, delivery: NotificationDelivery) -> None:
        """Agregar entrega."""
        self.deliveries.append(delivery)
        self.updated_at = datetime.now()
    
    def mark_all_as_read(self) -> None:
        """Marcar todas las entregas como leídas."""
        for delivery in self.deliveries:
            if delivery.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]:
                delivery.mark_as_read()
        self.updated_at = datetime.now()
    
    def get_read_status(self) -> bool:
        """Obtener estado de lectura general."""
        if not self.deliveries:
            return False
        
        # Se considera leída si al menos una entrega fue leída
        return any(delivery.status == NotificationStatus.READ for delivery in self.deliveries)
    
    def get_delivery_status_summary(self) -> Dict[str, int]:
        """Obtener resumen de estados de entrega."""
        summary = {status.value: 0 for status in NotificationStatus}
        
        for delivery in self.deliveries:
            summary[delivery.status.value] += 1
        
        return summary
    
    def render_content(self) -> Dict[str, str]:
        """Renderizar contenido usando plantilla."""
        if self.template:
            return self.template.render(self.context_data)
        
        return {
            'subject': self.title,
            'body': self.message
        }
    
    def add_tag(self, tag: str) -> None:
        """Agregar etiqueta."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Remover etiqueta."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def has_tag(self, tag: str) -> bool:
        """Verificar si tiene una etiqueta."""
        return tag in self.tags
    
    def can_retry_failed_deliveries(self) -> bool:
        """Verificar si se pueden reintentar entregas fallidas."""
        if self.is_expired():
            return False
        
        failed_deliveries = [
            d for d in self.deliveries 
            if d.status == NotificationStatus.FAILED and d.attempts < 3
        ]
        
        return len(failed_deliveries) > 0
    
    def get_failed_deliveries(self) -> List[NotificationDelivery]:
        """Obtener entregas fallidas."""
        return [
            d for d in self.deliveries 
            if d.status == NotificationStatus.FAILED
        ]
    
    def calculate_success_rate(self) -> float:
        """Calcular tasa de éxito de entregas."""
        if not self.deliveries:
            return 0.0
        
        successful = len([
            d for d in self.deliveries 
            if d.status in [NotificationStatus.DELIVERED, NotificationStatus.READ]
        ])
        
        return (successful / len(self.deliveries)) * 100


@dataclass
class NotificationSubscription:
    """Suscripción a notificaciones."""
    id: UUID
    user_id: UUID
    notification_types: List[NotificationType]
    channels: List[NotificationChannel]
    is_active: bool
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
    
    def allows_notification_type(self, notification_type: NotificationType) -> bool:
        """Verificar si permite un tipo de notificación."""
        return self.is_active and notification_type in self.notification_types
    
    def allows_channel(self, channel: NotificationChannel) -> bool:
        """Verificar si permite un canal."""
        return self.is_active and channel in self.channels
    
    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Actualizar preferencias."""
        self.preferences.update(new_preferences)
        self.updated_at = datetime.now()


@dataclass
class NotificationBatch:
    """Lote de notificaciones."""
    id: UUID
    name: str
    description: Optional[str]
    notification_ids: List[UUID]
    created_by: UUID
    status: str  # pending, processing, completed, failed
    total_notifications: int
    sent_notifications: int
    failed_notifications: int
    created_at: datetime
    completed_at: Optional[datetime]
    
    def __post_init__(self):
        if self.notification_ids is None:
            self.notification_ids = []
        self.total_notifications = len(self.notification_ids)
    
    def add_notification(self, notification_id: UUID) -> None:
        """Agregar notificación al lote."""
        if notification_id not in self.notification_ids:
            self.notification_ids.append(notification_id)
            self.total_notifications = len(self.notification_ids)
    
    def calculate_progress(self) -> float:
        """Calcular progreso del lote."""
        if self.total_notifications == 0:
            return 100.0
        
        completed = self.sent_notifications + self.failed_notifications
        return (completed / self.total_notifications) * 100
    
    def is_completed(self) -> bool:
        """Verificar si el lote está completado."""
        return self.calculate_progress() >= 100.0
