"""
Notification URLs Configuration.
Configuración de URLs para notificaciones.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.notifications.presentation.views import (
    NotificationViewSet, NotificationBroadcastViewSet
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'broadcast', NotificationBroadcastViewSet, basename='notification-broadcast')

app_name = 'notifications'

urlpatterns = [
    # API REST endpoints
    path('api/v1/', include(router.urls)),
    
    # Endpoints específicos adicionales
    path('api/v1/notifications/mark-as-read/<uuid:pk>/', 
         NotificationViewSet.as_view({'post': 'mark_as_read'}), 
         name='notification-mark-as-read'),
    
    path('api/v1/notifications/mark-all-as-read/', 
         NotificationViewSet.as_view({'post': 'mark_all_as_read'}), 
         name='notification-mark-all-as-read'),
    
    path('api/v1/notifications/unread-count/', 
         NotificationViewSet.as_view({'get': 'unread_count'}), 
         name='notification-unread-count'),
    
    path('api/v1/notifications/stats/', 
         NotificationViewSet.as_view({'get': 'stats'}), 
         name='notification-stats'),
    
    path('api/v1/notifications/summary/', 
         NotificationViewSet.as_view({'get': 'summary'}), 
         name='notification-summary'),
    
    path('api/v1/notifications/cleanup-expired/', 
         NotificationViewSet.as_view({'post': 'cleanup_expired'}), 
         name='notification-cleanup-expired'),
    
    # Broadcast endpoints
    path('api/v1/broadcast/all/', 
         NotificationBroadcastViewSet.as_view({'post': 'broadcast_all'}), 
         name='broadcast-all'),
    
    path('api/v1/broadcast/group/', 
         NotificationBroadcastViewSet.as_view({'post': 'broadcast_group'}), 
         name='broadcast-group'),
]
