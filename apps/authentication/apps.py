"""
Authentication App Configuration.
Configuración de la aplicación de autenticación.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuración de la app de autenticación."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentication'
    
    def ready(self):
        """Ejecutar cuando la app esté lista."""
        # Importar signals si los hay
        try:
            from . import signals
        except ImportError:
            pass
