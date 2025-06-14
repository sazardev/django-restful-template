"""
Users Application Configuration.
Sistema de gestión de usuarios con roles y permisos granulares.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuración de la aplicación de usuarios."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Sistema de Usuarios'
    
    def ready(self):
        """Inicialización de la aplicación."""
        import apps.users.infrastructure.signals  # noqa
