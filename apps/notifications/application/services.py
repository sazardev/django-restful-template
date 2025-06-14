"""
Notification Application Services.
Servicios de aplicación para notificaciones.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.notifications.application.entities import SimpleNotificationEntity as NotificationEntity
from apps.notifications.domain.entities import NotificationType, NotificationPriority
from apps.notifications.infrastructure.repository import (
    NotificationRepository, NotificationChannelRepository
)
from shared.domain.exceptions import ValidationError

logger = logging.getLogger(__name__)


class NotificationApplicationService:
    """Servicio de aplicación para notificaciones."""
    
    def __init__(self):
        self.notification_repo = NotificationRepository()
        self.channel_repo = NotificationChannelRepository()
        self.channel_layer = get_channel_layer()
    
    def create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        expires_in_hours: Optional[int] = None,
        created_by_id: Optional[UUID] = None,
        send_realtime: bool = True
    ) -> NotificationEntity:
        """
        Crear y enviar una nueva notificación.
        
        Args:
            user_id: ID del usuario destinatario
            title: Título de la notificación
            message: Mensaje de la notificación
            notification_type: Tipo de notificación
            priority: Prioridad de la notificación
            data: Datos adicionales (opcional)
            expires_in_hours: Horas hasta expiración (opcional)
            created_by_id: ID del usuario que crea la notificación (opcional)
            send_realtime: Si enviar en tiempo real por WebSocket
        
        Returns:
            NotificationEntity: La notificación creada
        """
        if not title or not message:
            raise ValidationError("Título y mensaje son requeridos")
        
        expires_at = None
        if expires_in_hours:
            expires_at = timezone.now() + timedelta(hours=expires_in_hours)
        
        # Crear notificación
        notification = self.notification_repo.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            data=data,
            expires_at=expires_at,
            created_by_id=created_by_id
        )
        
        # Enviar en tiempo real si está habilitado
        if send_realtime:
            self.send_realtime_notification(notification)
        
        logger.info(f"Notificación creada: {notification.id} para usuario {user_id}")
        return notification
    
    def send_realtime_notification(self, notification: NotificationEntity) -> None:
        """Enviar notificación en tiempo real por WebSocket."""
        if not self.channel_layer:
            logger.warning("Channel layer no disponible para notificaciones en tiempo real")
            return
        
        try:
            user_group_name = f"user_{notification.user_id}"
            
            # Enviar notificación al grupo del usuario
            async_to_sync(self.channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'notification_message',
                    'notification': notification.to_dict()
                }
            )
            
            # Enviar actualización del contador
            unread_count = self.notification_repo.get_unread_count(notification.user_id)
            async_to_sync(self.channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'notification_count_update',
                    'count': unread_count
                }
            )
            
            logger.debug(f"Notificación enviada en tiempo real: {notification.id}")
        
        except Exception as e:
            logger.error(f"Error enviando notificación en tiempo real: {e}")
    
    def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[NotificationEntity]:
        """Obtener notificaciones de un usuario."""
        return self.notification_repo.get_user_notifications(
            user_id, unread_only, limit, offset
        )
    
    def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Marcar notificación como leída con validación de usuario."""
        notification = self.notification_repo.get_notification(notification_id)
        
        if not notification:
            raise ValidationError("Notificación no encontrada")
        
        if notification.user_id != user_id:
            raise ValidationError("No tienes permisos para esta notificación")
        
        success = self.notification_repo.mark_as_read(notification_id)
        
        if success:
            # Enviar actualización del contador en tiempo real
            self._send_count_update(user_id)
        
        return success
    
    def mark_all_as_read(self, user_id: UUID) -> int:
        """Marcar todas las notificaciones de un usuario como leídas."""
        count = self.notification_repo.mark_all_as_read(user_id)
        
        if count > 0:
            # Enviar actualización del contador en tiempo real
            self._send_count_update(user_id)
        
        return count
    
    def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Eliminar notificación con validación de usuario."""
        notification = self.notification_repo.get_notification(notification_id)
        
        if not notification:
            raise ValidationError("Notificación no encontrada")
        
        if notification.user_id != user_id:
            raise ValidationError("No tienes permisos para esta notificación")
        
        success = self.notification_repo.delete_notification(notification_id)
        
        if success:
            # Enviar actualización del contador en tiempo real
            self._send_count_update(user_id)
        
        return success
    
    def get_unread_count(self, user_id: UUID) -> int:
        """Obtener cantidad de notificaciones no leídas."""
        return self.notification_repo.get_unread_count(user_id)
    
    def cleanup_expired_notifications(self) -> int:
        """Limpiar notificaciones expiradas."""
        return self.notification_repo.cleanup_expired_notifications()
    
    def _send_count_update(self, user_id: UUID) -> None:
        """Enviar actualización del contador de notificaciones."""
        if not self.channel_layer:
            return
        
        try:
            unread_count = self.notification_repo.get_unread_count(user_id)
            user_group_name = f"user_{user_id}"
            
            async_to_sync(self.channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'notification_count_update',
                    'count': unread_count
                }
            )
        except Exception as e:
            logger.error(f"Error enviando actualización de contador: {e}")


class NotificationTemplateService:
    """Servicio para plantillas de notificación."""
    
    def create_from_template(
        self,
        template_name: str,
        user_id: UUID,
        context: Dict[str, Any],
        created_by_id: Optional[UUID] = None
    ) -> NotificationEntity:
        """Crear notificación desde plantilla."""
        # TODO: Implementar lógica de plantillas
        # Por ahora, crear notificación básica
        service = NotificationApplicationService()
        
        return service.create_notification(
            user_id=user_id,
            title=f"Notificación desde plantilla: {template_name}",
            message=f"Datos: {context}",
            created_by_id=created_by_id
        )


class NotificationBroadcastService:
    """Servicio para broadcast de notificaciones."""
    
    def __init__(self):
        self.notification_service = NotificationApplicationService()
        self.channel_layer = get_channel_layer()
    
    def broadcast_to_all_users(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        created_by_id: Optional[UUID] = None
    ) -> int:
        """Enviar notificación a todos los usuarios."""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        users = User.objects.filter(is_active=True)
        
        count = 0
        for user in users:
            try:
                self.notification_service.create_notification(
                    user_id=user.id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    data=data,
                    created_by_id=created_by_id
                )
                count += 1
            except Exception as e:
                logger.error(f"Error creando notificación para usuario {user.id}: {e}")
        
        logger.info(f"Broadcast enviado a {count} usuarios")
        return count
    
    def broadcast_to_user_group(
        self,
        group_name: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        created_by_id: Optional[UUID] = None
    ) -> int:
        """Enviar notificación a un grupo de usuarios."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        
        try:
            User = get_user_model()
            group = Group.objects.get(name=group_name)
            users = User.objects.filter(groups=group, is_active=True)
            
            count = 0
            for user in users:
                try:
                    self.notification_service.create_notification(
                        user_id=user.id,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        priority=priority,
                        data=data,
                        created_by_id=created_by_id
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error creando notificación para usuario {user.id}: {e}")
            
            logger.info(f"Broadcast enviado a {count} usuarios del grupo {group_name}")
            return count
        
        except Group.DoesNotExist:
            logger.error(f"Grupo no encontrado: {group_name}")
            return 0


class NotificationAuctionService:
    """Servicio específico para notificaciones de subastas."""
    
    def __init__(self):
        self.notification_service = NotificationApplicationService()
    
    def notify_auction_created(self, auction_data: Dict[str, Any]) -> None:
        """Notificar creación de subasta a usuarios interesados."""
        # TODO: Implementar lógica para determinar usuarios interesados
        # Por ejemplo, usuarios que siguen el vehículo o categoría
        pass
    
    def notify_new_bid(
        self,
        auction_id: UUID,
        bidder_id: UUID,
        previous_bidder_id: Optional[UUID],
        bid_amount: float
    ) -> None:
        """Notificar nueva puja en subasta."""
        # Notificar al pujador anterior que fue superado
        if previous_bidder_id and previous_bidder_id != bidder_id:
            self.notification_service.create_notification(
                user_id=previous_bidder_id,
                title="¡Tu puja ha sido superada!",
                message=f"Alguien ha pujado más alto en la subasta. Nueva puja: ${bid_amount:,.2f}",
                notification_type=NotificationType.WARNING,
                priority=NotificationPriority.HIGH,
                data={
                    'auction_id': str(auction_id),
                    'new_bid_amount': bid_amount,
                    'action': 'bid_outbid'
                }
            )
    
    def notify_auction_won(self, auction_id: UUID, winner_id: UUID, final_amount: float) -> None:
        """Notificar que el usuario ganó la subasta."""
        self.notification_service.create_notification(
            user_id=winner_id,
            title="¡Felicidades! Has ganado la subasta",
            message=f"Has ganado la subasta con una puja de ${final_amount:,.2f}",
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.HIGH,
            data={
                'auction_id': str(auction_id),
                'final_amount': final_amount,
                'action': 'auction_won'
            }
        )
    
    def notify_auction_ended(self, auction_id: UUID, participants: List[UUID]) -> None:
        """Notificar fin de subasta a todos los participantes."""
        for participant_id in participants:
            self.notification_service.create_notification(
                user_id=participant_id,
                title="Subasta finalizada",
                message="La subasta en la que participaste ha finalizado.",
                notification_type=NotificationType.INFO,
                data={
                    'auction_id': str(auction_id),
                    'action': 'auction_ended'
                }
            )
