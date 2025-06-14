"""
Vehicle Application Layer.
Capa de aplicación para el sistema de vehículos.
"""

from .dtos import (
    VehicleCreateDTO,
    VehicleUpdateDTO,
    VehicleResponseDTO,
    VehicleListResponseDTO,
    VehicleSpecificationsDTO,
    GPSLocationDTO,
    MaintenanceRecordDTO,
    VehicleFilterDTO,
    VehicleAnalyticsDTO
)
from .services import (
    VehicleService,
    VehicleLocationService,
    VehicleMaintenanceService,
    VehicleAnalyticsService
)

__all__ = [
    # DTOs
    'VehicleCreateDTO',
    'VehicleUpdateDTO',
    'VehicleResponseDTO',
    'VehicleListResponseDTO',
    'VehicleSpecificationsDTO',
    'GPSLocationDTO',
    'MaintenanceRecordDTO',
    'VehicleFilterDTO',
    'VehicleAnalyticsDTO',
    # Services
    'VehicleService',
    'VehicleLocationService',
    'VehicleMaintenanceService',
    'VehicleAnalyticsService',
]
