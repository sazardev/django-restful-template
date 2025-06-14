"""
WebSocket Consumers for Real-time Notifications.
Consumidores WebSocket para notificaciones en tiempo real.
"""

import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from apps.notifications.infrastructure.repository import (
    NotificationRepository, NotificationChannelRepository
)
from apps.notifications.domain.entities import NotificationType

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer para notificaciones en tiempo real."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_group_name = None
        self.notification_repo = NotificationRepository()
        self.channel_repo = NotificationChannelRepository()
    
    async def connect(self):
        """Conectar usuario al WebSocket."""
        self.user = self.scope["user"]
        
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        # Crear grupo único por usuario
        self.user_group_name = f"user_{self.user.id}"
        
        # Unirse al grupo de notificaciones del usuario
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Registrar canal de WebSocket
        await self.register_websocket_channel()
        
        # Enviar notificaciones pendientes
        await self.send_pending_notifications()
        
        logger.info(f"Usuario {self.user.email} conectado a notificaciones WebSocket")
    
    async def disconnect(self, close_code):
        """Desconectar usuario del WebSocket."""
        if self.user_group_name:
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        # Desactivar canal de WebSocket
        await self.deactivate_websocket_channel()
        
        if self.user:
            logger.info(f"Usuario {self.user.email} desconectado de notificaciones WebSocket")
    
    async def receive(self, text_data):
        """Recibir mensaje del cliente."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_as_read':
                await self.handle_mark_as_read(data)
            elif message_type == 'mark_all_as_read':
                await self.handle_mark_all_as_read()
            elif message_type == 'get_notifications':
                await self.handle_get_notifications(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send_error(f"Tipo de mensaje no reconocido: {message_type}")
        
        except json.JSONDecodeError:
            await self.send_error("Formato JSON inválido")
        except Exception as e:
            logger.error(f"Error en receive: {e}")
            await self.send_error("Error interno del servidor")
    
    async def notification_message(self, event):
        """Enviar notificación al cliente."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def notification_count_update(self, event):
        """Enviar actualización del contador de notificaciones."""
        await self.send(text_data=json.dumps({
            'type': 'notification_count',
            'count': event['count']
        }))
    
    async def handle_mark_as_read(self, data: Dict[str, Any]):
        """Manejar marcar notificación como leída."""
        try:
            notification_id = data.get('notification_id')
            if not notification_id:
                await self.send_error("ID de notificación requerido")
                return
            
            success = await database_sync_to_async(
                self.notification_repo.mark_as_read
            )(UUID(notification_id))
            
            if success:
                # Enviar contador actualizado
                unread_count = await database_sync_to_async(
                    self.notification_repo.get_unread_count
                )(self.user.id)
                
                await self.send(text_data=json.dumps({
                    'type': 'mark_as_read_success',
                    'notification_id': notification_id,
                    'unread_count': unread_count
                }))
            else:
                await self.send_error("No se pudo marcar la notificación como leída")
        
        except ValueError:
            await self.send_error("ID de notificación inválido")
        except Exception as e:
            logger.error(f"Error en mark_as_read: {e}")
            await self.send_error("Error interno del servidor")
    
    async def handle_mark_all_as_read(self):
        """Manejar marcar todas las notificaciones como leídas."""
        try:
            count = await database_sync_to_async(
                self.notification_repo.mark_all_as_read
            )(self.user.id)
            
            await self.send(text_data=json.dumps({
                'type': 'mark_all_as_read_success',
                'marked_count': count,
                'unread_count': 0
            }))
        
        except Exception as e:
            logger.error(f"Error en mark_all_as_read: {e}")
            await self.send_error("Error interno del servidor")
    
    async def handle_get_notifications(self, data: Dict[str, Any]):
        """Manejar obtener notificaciones."""
        try:
            limit = data.get('limit', 20)
            offset = data.get('offset', 0)
            unread_only = data.get('unread_only', False)
            
            notifications = await database_sync_to_async(
                self.notification_repo.get_user_notifications
            )(self.user.id, unread_only, limit, offset)
            
            notifications_data = [notification.to_dict() for notification in notifications]
            
            await self.send(text_data=json.dumps({
                'type': 'notifications',
                'notifications': notifications_data,
                'limit': limit,
                'offset': offset,
                'unread_only': unread_only
            }))
        
        except Exception as e:
            logger.error(f"Error en get_notifications: {e}")
            await self.send_error("Error interno del servidor")
    
    async def send_pending_notifications(self):
        """Enviar notificaciones pendientes al conectar."""
        try:
            notifications = await database_sync_to_async(
                self.notification_repo.get_user_notifications
            )(self.user.id, unread_only=True, limit=10)
            
            unread_count = await database_sync_to_async(
                self.notification_repo.get_unread_count
            )(self.user.id)
            
            await self.send(text_data=json.dumps({
                'type': 'initial_notifications',
                'notifications': [notification.to_dict() for notification in notifications],
                'unread_count': unread_count
            }))
        
        except Exception as e:
            logger.error(f"Error enviando notificaciones pendientes: {e}")
    
    async def send_error(self, message: str):
        """Enviar mensaje de error al cliente."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    @database_sync_to_async
    def register_websocket_channel(self):
        """Registrar canal de WebSocket en la base de datos."""
        try:
            self.channel_repo.create_channel(
                user_id=self.user.id,
                channel_type='websocket',
                channel_identifier=self.channel_name,
                settings={'group_name': self.user_group_name}
            )
        except Exception as e:
            logger.error(f"Error registrando canal WebSocket: {e}")
    
    @database_sync_to_async
    def deactivate_websocket_channel(self):
        """Desactivar canal de WebSocket en la base de datos."""
        try:
            channels = self.channel_repo.get_user_channels(self.user.id, active_only=True)
            for channel in channels:
                if 'websocket' in channel.channel_name and self.channel_name in channel.channel_name:
                    self.channel_repo.deactivate_channel(channel.id)
                    break
        except Exception as e:
            logger.error(f"Error desactivando canal WebSocket: {e}")


class NotificationBroadcastConsumer(AsyncWebsocketConsumer):
    """Consumer para broadcasts de notificaciones administrativas."""
    
    async def connect(self):
        """Conectar al canal de broadcast."""
        user = self.scope["user"]
        
        if isinstance(user, AnonymousUser) or not user.is_staff:
            await self.close()
            return
        
        await self.channel_layer.group_add("admin_broadcast", self.channel_name)
        await self.accept()
        
        logger.info(f"Admin {user.email} conectado al canal de broadcast")
    
    async def disconnect(self, close_code):
        """Desconectar del canal de broadcast."""
        await self.channel_layer.group_discard("admin_broadcast", self.channel_name)
    
    async def receive(self, text_data):
        """Recibir mensaje de broadcast del admin."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'broadcast_notification':
                await self.handle_broadcast_notification(data)
            elif message_type == 'system_maintenance':
                await self.handle_system_maintenance(data)
        
        except json.JSONDecodeError:
            await self.send_error("Formato JSON inválido")
        except Exception as e:
            logger.error(f"Error en broadcast receive: {e}")
            await self.send_error("Error interno del servidor")
    
    async def handle_broadcast_notification(self, data: Dict[str, Any]):
        """Manejar notificación broadcast."""
        # Implementar lógica de broadcast a todos los usuarios conectados
        pass
    
    async def handle_system_maintenance(self, data: Dict[str, Any]):
        """Manejar notificación de mantenimiento del sistema."""
        # Implementar lógica de notificación de mantenimiento
        pass
    
    async def send_error(self, message: str):
        """Enviar mensaje de error."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
