"""
Vehicle Infrastructure Layer.
Capa de infraestructura para el sistema de vehículos.
"""

from .models import Vehicle, VehicleLocation, MaintenanceRecord
from .repository import VehicleRepository
from .services import (
    VehicleLocationService,
    VehicleMaintenanceService,
    VehicleAnalyticsService,
    VehicleEventService
)

__all__ = [
    # Models
    'Vehicle',
    'VehicleLocation', 
    'MaintenanceRecord',
    # Repository
    'VehicleRepository',
    # Services
    'VehicleLocationService',
    'VehicleMaintenanceService',
    'VehicleAnalyticsService',
    'VehicleEventService',
]
