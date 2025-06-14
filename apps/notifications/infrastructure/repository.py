"""
Notification Repository Implementation.
Implementación del repositorio de notificaciones.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from apps.notifications.application.entities import SimpleNotificationEntity as NotificationEntity
from apps.notifications.domain.entities import (
    NotificationChannelEntity, NotificationType,
    NotificationPriority, NotificationStatus
)
from apps.notifications.infrastructure.models import (
    NotificationModel, NotificationChannelModel, NotificationTemplateModel,
    NotificationDeliveryModel
)

User = get_user_model()


class NotificationRepository:
    """Repositorio de notificaciones."""
    
    def create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        created_by_id: Optional[UUID] = None
    ) -> NotificationEntity:
        """Crear una nueva notificación."""
        notification = NotificationModel.objects.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type.value,
            priority=priority.value,
            data=data or {},
            expires_at=expires_at,
            created_by_id=created_by_id
        )
        return self._model_to_entity(notification)
    
    def get_notification(self, notification_id: UUID) -> Optional[NotificationEntity]:
        """Obtener notificación por ID."""
        try:
            notification = NotificationModel.objects.get(id=notification_id)
            return self._model_to_entity(notification)
        except NotificationModel.DoesNotExist:
            return None
    
    def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[NotificationEntity]:
        """Obtener notificaciones de un usuario."""
        queryset = NotificationModel.objects.filter(user_id=user_id)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        queryset = queryset.order_by('-created_at')
        
        if offset:
            queryset = queryset[offset:]
        
        if limit:
            queryset = queryset[:limit]
        
        return [self._model_to_entity(notification) for notification in queryset]
    
    def mark_as_read(self, notification_id: UUID) -> bool:
        """Marcar notificación como leída."""
        try:
            notification = NotificationModel.objects.get(id=notification_id)
            notification.mark_as_read()
            return True
        except NotificationModel.DoesNotExist:
            return False
    
    def mark_all_as_read(self, user_id: UUID) -> int:
        """Marcar todas las notificaciones de un usuario como leídas."""
        return NotificationModel.objects.filter(
            user_id=user_id,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now(),
            status=NotificationStatus.READ.value
        )
    
    def delete_notification(self, notification_id: UUID) -> bool:
        """Eliminar notificación."""
        try:
            NotificationModel.objects.get(id=notification_id).delete()
            return True
        except NotificationModel.DoesNotExist:            return False
    
    def get_unread_count(self, user_id: UUID) -> int:
        """Obtener cantidad de notificaciones no leídas."""
        return NotificationModel.objects.filter(
            user_id=user_id,
            is_read=False
        ).count()
    
    def cleanup_expired_notifications(self) -> int:
        """Limpiar notificaciones expiradas."""
        now = timezone.now()
        expired_notifications = NotificationModel.objects.filter(
            expires_at__lt=now,
            status__in=[NotificationStatus.PENDING.value, NotificationStatus.SENT.value]
        )
        
        count = expired_notifications.count()
        expired_notifications.update(status=NotificationStatus.EXPIRED.value)
        return count
    
    def get_notifications_by_type(
        self,
        notification_type: NotificationType,
        limit: Optional[int] = None
    ) -> List[NotificationEntity]:
        """Obtener notificaciones por tipo."""
        queryset = NotificationModel.objects.filter(
            notification_type=notification_type.value
        ).order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return [self._model_to_entity(notification) for notification in queryset]    
    def _model_to_entity(self, model: NotificationModel) -> NotificationEntity:
        """Convertir modelo a entidad."""
        return NotificationEntity(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            message=model.message,
            notification_type=NotificationType(model.notification_type),
            priority=NotificationPriority(model.priority),
            data=model.data,
            is_read=model.is_read,
            created_at=model.created_at,
            read_at=model.read_at,
            expires_at=model.expires_at
        )


class NotificationChannelRepository:
    """Repositorio de canales de notificación."""
    
    def create_channel(
        self,
        user_id: UUID,
        channel_type: str,
        channel_identifier: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> NotificationChannelEntity:
        """Crear canal de notificación."""
        channel = NotificationChannelModel.objects.create(
            user_id=user_id,
            channel_type=channel_type,
            channel_identifier=channel_identifier,
            settings=settings or {}
        )
        return self._model_to_entity(channel)
    
    def get_user_channels(
        self,
        user_id: UUID,
        active_only: bool = True
    ) -> List[NotificationChannelEntity]:
        """Obtener canales de un usuario."""
        queryset = NotificationChannelModel.objects.filter(user_id=user_id)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return [self._model_to_entity(channel) for channel in queryset]
    
    def get_channel(self, channel_id: UUID) -> Optional[NotificationChannelEntity]:
        """Obtener canal por ID."""
        try:
            channel = NotificationChannelModel.objects.get(id=channel_id)
            return self._model_to_entity(channel)
        except NotificationChannelModel.DoesNotExist:
            return None
    
    def update_last_activity(self, channel_id: UUID) -> bool:
        """Actualizar última actividad del canal."""
        try:
            NotificationChannelModel.objects.filter(id=channel_id).update(
                last_used_at=timezone.now()
            )
            return True
        except NotificationChannelModel.DoesNotExist:
            return False
    
    def deactivate_channel(self, channel_id: UUID) -> bool:
        """Desactivar canal."""
        try:
            NotificationChannelModel.objects.filter(id=channel_id).update(
                is_active=False
            )
            return True
        except NotificationChannelModel.DoesNotExist:
            return False
    
    def _model_to_entity(self, model: NotificationChannelModel) -> NotificationChannelEntity:
        """Convertir modelo a entidad."""
        return NotificationChannelEntity(
            id=model.id,
            user_id=model.user_id,
            channel_name=f"{model.channel_type}:{model.channel_identifier}",
            is_active=model.is_active,
            created_at=model.created_at,
            last_activity=model.last_used_at
        )
