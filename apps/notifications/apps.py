"""
Notifications App Configuration.
Configuración de la aplicación de notificaciones.
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuración de la app de notificaciones."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'    
    def ready(self):
        """Ejecutar cuando la app esté lista."""
        try:
            from . import signals
            from .infrastructure import signals as infra_signals
        except ImportError:
            pass
