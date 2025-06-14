"""
Vehicle Domain Module.
Módulo de dominio para el sistema de vehículos.
"""

from .entities import (
    VehicleEntity,
    VehicleSpecifications,
    GPSLocation,
    MaintenanceRecord,
    VehicleType,
    VehicleStatus,
    FuelType
)
from .interfaces import (
    VehicleRepositoryInterface,
    VehicleLocationServiceInterface,
    VehicleMaintenanceServiceInterface,
    VehicleAnalyticsServiceInterface,
    VehicleEventServiceInterface
)
from .exceptions import (
    VehicleException,
    VehicleNotFound,
    VehicleAlreadyExists,
    VehicleNotAvailable,
    VehicleInUse,
    InvalidVehicleOperation,
    VehicleMaintenanceError,
    InvalidLocationData,
    VehicleCapacityExceeded,
    MaintenanceRecordNotFound,
    InvalidVehicleSpecifications,
    VehicleRegistrationExpired,
    VehicleInsuranceExpired
)

__all__ = [
    # Entities
    'VehicleEntity',
    'VehicleSpecifications',
    'GPSLocation',
    'MaintenanceRecord',
    'VehicleType',
    'VehicleStatus',
    'FuelType',
    # Interfaces
    'VehicleRepositoryInterface',
    'VehicleLocationServiceInterface',
    'VehicleMaintenanceServiceInterface',
    'VehicleAnalyticsServiceInterface',
    'VehicleEventServiceInterface',
    # Exceptions
    'VehicleException',
    'VehicleNotFound',
    'VehicleAlreadyExists',
    'VehicleNotAvailable',
    'VehicleInUse',
    'InvalidVehicleOperation',
    'VehicleMaintenanceError',
    'InvalidLocationData',
    'VehicleCapacityExceeded',
    'MaintenanceRecordNotFound',
    'InvalidVehicleSpecifications',
    'VehicleRegistrationExpired',
    'VehicleInsuranceExpired',
]
