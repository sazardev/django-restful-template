"""
Notification Infrastructure Signals.
Señales de infraestructura para notificaciones.
"""

import logging
from typing import Dict, Any
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.notifications.infrastructure.models import (
    NotificationModel, NotificationChannelModel, NotificationDeliveryModel
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=NotificationModel)
def notification_model_saved(sender, instance, created, **kwargs):
    """
    Signal cuando se guarda un modelo de notificación.
    Actualiza estadísticas y envía eventos.
    """
    if created:
        logger.debug(f"NotificationModel creado: {instance.id}")
        
        # Enviar evento de notificación en tiempo real
        send_realtime_notification_event(instance)
        
        # Actualizar contador de notificaciones no leídas
        send_unread_count_update(instance.user_id)
    else:
        logger.debug(f"NotificationModel actualizado: {instance.id}")
        
        # Si se marcó como leída, actualizar contador
        if instance.is_read and instance.read_at:
            send_unread_count_update(instance.user_id)


@receiver(post_delete, sender=NotificationModel)
def notification_model_deleted(sender, instance, **kwargs):
    """
    Signal cuando se elimina un modelo de notificación.
    Actualiza contadores.
    """
    logger.debug(f"NotificationModel eliminado: {instance.id}")
    
    # Actualizar contador de notificaciones no leídas
    send_unread_count_update(instance.user_id)


@receiver(post_save, sender=NotificationChannelModel)
def notification_channel_saved(sender, instance, created, **kwargs):
    """
    Signal cuando se guarda un canal de notificación.
    """
    if created:
        logger.debug(f"NotificationChannelModel creado: {instance.id}")
        
        # Registrar actividad del canal
        if instance.channel_type == 'websocket':
            instance.last_used_at = timezone.now()
            instance.save(update_fields=['last_used_at'])


@receiver(post_save, sender=NotificationDeliveryModel)
def notification_delivery_saved(sender, instance, created, **kwargs):
    """
    Signal cuando se guarda una entrega de notificación.
    """
    if created:
        logger.debug(f"NotificationDeliveryModel creado: {instance.id}")
    
    # Actualizar estadísticas de entrega
    if instance.status == 'delivered' and not instance.delivered_at:
        instance.delivered_at = timezone.now()
        instance.save(update_fields=['delivered_at'])


def send_realtime_notification_event(notification: NotificationModel) -> None:
    """
    Enviar evento de notificación en tiempo real por WebSocket.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer no disponible para eventos en tiempo real")
        return
    
    try:
        user_group_name = f"user_{notification.user_id}"
        
        notification_data = {
            'id': str(notification.id),
            'user_id': str(notification.user_id),
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'priority': notification.priority,
            'data': notification.data or {},
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
        }
        
        # Enviar notificación al grupo del usuario
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'notification_message',
                'notification': notification_data
            }
        )
        
        logger.debug(f"Evento de notificación enviado en tiempo real: {notification.id}")
    
    except Exception as e:
        logger.error(f"Error enviando evento de notificación en tiempo real: {e}")


def send_unread_count_update(user_id) -> None:
    """
    Enviar actualización del contador de notificaciones no leídas.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        # Calcular contador actual
        unread_count = NotificationModel.objects.filter(
            user_id=user_id,
            is_read=False
        ).count()
        
        user_group_name = f"user_{user_id}"
        
        # Enviar actualización del contador
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'notification_count_update',
                'count': unread_count
            }
        )
        
        logger.debug(f"Contador de notificaciones actualizado para usuario {user_id}: {unread_count}")
    
    except Exception as e:
        logger.error(f"Error enviando actualización de contador: {e}")


def send_notification_status_update(notification_id, status: str) -> None:
    """
    Enviar actualización del estado de una notificación.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        notification = NotificationModel.objects.get(id=notification_id)
        user_group_name = f"user_{notification.user_id}"
        
        # Enviar actualización del estado
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'notification_status_update',
                'notification_id': str(notification_id),
                'status': status,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.debug(f"Estado de notificación actualizado: {notification_id} -> {status}")
    
    except NotificationModel.DoesNotExist:
        logger.warning(f"Notificación no encontrada para actualizar estado: {notification_id}")
    except Exception as e:
        logger.error(f"Error enviando actualización de estado: {e}")


def broadcast_system_notification(
    title: str,
    message: str,
    notification_type: str = 'info',
    data: Dict[str, Any] = None
) -> None:
    """
    Enviar notificación del sistema a todos los usuarios conectados.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    try:
        system_notification = {
            'id': 'system_broadcast',
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'priority': 3,  # High priority for system messages
            'data': data or {},
            'is_system': True,
            'created_at': timezone.now().isoformat()
        }
        
        # Enviar a canal de broadcast general
        async_to_sync(channel_layer.group_send)(
            'system_broadcast',
            {
                'type': 'system_notification',
                'notification': system_notification
            }
        )
        
        logger.info(f"Notificación del sistema enviada: {title}")
    
    except Exception as e:
        logger.error(f"Error enviando notificación del sistema: {e}")


def send_maintenance_notification(message: str, scheduled_time: str = None) -> None:
    """
    Enviar notificación de mantenimiento del sistema.
    """
    data = {'maintenance': True}
    if scheduled_time:
        data['scheduled_time'] = scheduled_time
    
    broadcast_system_notification(
        title="Mantenimiento del Sistema",
        message=message,
        notification_type='warning',
        data=data
    )
