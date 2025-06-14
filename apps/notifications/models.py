"""
Notification Models.
Exposición de modelos de notificaciones para Django.
"""

from apps.notifications.infrastructure.models import (
    NotificationModel,
    NotificationChannelModel,
    NotificationTemplateModel,
    NotificationDeliveryModel
)

# Alias para facilitar importaciones
Notification = NotificationModel
NotificationChannel = NotificationChannelModel
NotificationTemplate = NotificationTemplateModel
NotificationDelivery = NotificationDeliveryModel

__all__ = [
    'NotificationModel',
    'NotificationChannelModel', 
    'NotificationTemplateModel',
    'NotificationDeliveryModel',
    'Notification',
    'NotificationChannel',
    'NotificationTemplate',
    'NotificationDelivery',
]
