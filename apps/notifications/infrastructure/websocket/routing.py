"""
WebSocket URL Routing.
Configuración de rutas WebSocket para notificaciones.
"""

from django.urls import path
from apps.notifications.infrastructure.consumers import (
    NotificationConsumer, NotificationBroadcastConsumer
)

websocket_urlpatterns = [
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    path('ws/notifications/broadcast/', NotificationBroadcastConsumer.as_asgi()),
]
