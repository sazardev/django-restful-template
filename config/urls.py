"""
URL configuration for Logistics API.
Professional Django REST API with clean architecture and dependency injection.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Health check imports
from apps.shared.views.health import health_check, health_check_detailed
from apps.shared.views.websocket_health import websocket_health

# API URLs
api_v1_patterns = [
    # Authentication
    path('', include('apps.authentication.urls')),
    
    # Users Management
    path('', include('apps.users.urls')),
    
    # Vehicles Management
    path('', include('apps.vehicles.urls')),
      # Auctions System
    path('', include('apps.auctions.urls')),
      # Notifications
    path('', include('apps.notifications.urls')),
]

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Health checks
    path('health/', health_check, name='health_check'),
    path('api/health/', health_check_detailed, name='health_check_detailed'),
    path('ws/health/', websocket_health, name='websocket_health'),
    
    # API v1
    path('api/v1/', include(api_v1_patterns)),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Custom admin configuration
admin.site.site_header = "Logistics API Administration"
admin.site.site_title = "Logistics API Admin"
admin.site.index_title = "Welcome to Logistics API Administration"
