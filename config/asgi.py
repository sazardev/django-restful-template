"""
ASGI config for Logistics API project.
It exposes the ASGI callable as a module-level variable named `application`.
"""

import os
import django

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
django.setup()

# Import after Django setup
from apps.notifications.infrastructure.websocket.routing import websocket_urlpatterns

# ASGI application
application = ProtocolTypeRouter({
    # HTTP requests
    "http": get_asgi_application(),
    
    # WebSocket connections
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
