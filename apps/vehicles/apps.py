"""
Vehicles Application Configuration.
Sistema de gestión de vehículos para la plataforma logística.
"""

from django.apps import AppConfig


class VehiclesConfig(AppConfig):
    """Configuración de la aplicación de vehículos."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vehicles'
    verbose_name = 'Sistema de Vehículos'
    
    def ready(self):
        """Inicialización de la aplicación."""
        import apps.vehicles.infrastructure.signals  # noqa
