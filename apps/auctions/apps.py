"""
Auctions App Configuration.
Configuración de la aplicación de subastas.
"""

from django.apps import AppConfig


class AuctionsConfig(AppConfig):
    """Configuración de la app de subastas."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auctions'
    verbose_name = 'Auctions'
    
    def ready(self):
        """Ejecutar cuando la app esté lista."""
        try:
            from . import signals
        except ImportError:
            pass
