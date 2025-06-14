"""
Vehicle Domain Interfaces.
Interfaces del dominio para el sistema de vehículos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from .entities import VehicleEntity, VehicleType, VehicleStatus, GPSLocation


class VehicleRepositoryInterface(ABC):
    """Interface para el repositorio de vehículos."""

    @abstractmethod
    async def create(self, vehicle: VehicleEntity) -> VehicleEntity:
        """Crear un nuevo vehículo."""
        pass

    @abstractmethod
    async def get_by_id(self, vehicle_id: UUID) -> Optional[VehicleEntity]:
        """Obtener vehículo por ID."""
        pass

    @abstractmethod
    async def get_by_license_plate(self, license_plate: str) -> Optional[VehicleEntity]:
        """Obtener vehículo por placa."""
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[VehicleEntity]:
        """Obtener lista de vehículos con filtros opcionales."""
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> List[VehicleEntity]:
        """Obtener vehículos por propietario."""
        pass

    @abstractmethod
    async def get_available_vehicles(
        self,
        vehicle_type: Optional[VehicleType] = None,
        min_weight_capacity: Optional[Decimal] = None,
        min_volume_capacity: Optional[Decimal] = None,
        near_location: Optional[GPSLocation] = None,
        radius_km: Optional[Decimal] = None
    ) -> List[VehicleEntity]:
        """Obtener vehículos disponibles con criterios específicos."""
        pass

    @abstractmethod
    async def get_vehicles_by_status(self, status: VehicleStatus) -> List[VehicleEntity]:
        """Obtener vehículos por estado."""
        pass

    @abstractmethod
    async def get_vehicles_needing_maintenance(self) -> List[VehicleEntity]:
        """Obtener vehículos que necesitan mantenimiento."""
        pass

    @abstractmethod
    async def update(self, vehicle: VehicleEntity) -> VehicleEntity:
        """Actualizar vehículo."""
        pass

    @abstractmethod
    async def delete(self, vehicle_id: UUID) -> bool:
        """Eliminar vehículo."""
        pass

    @abstractmethod
    async def count(self, filters: Optional[dict] = None) -> int:
        """Contar vehículos con filtros opcionales."""
        pass


class VehicleLocationServiceInterface(ABC):
    """Interface para el servicio de ubicación de vehículos."""

    @abstractmethod
    async def update_vehicle_location(
        self,
        vehicle_id: UUID,
        location: GPSLocation
    ) -> bool:
        """Actualizar ubicación de un vehículo."""
        pass

    @abstractmethod
    async def get_vehicles_near_location(
        self,
        location: GPSLocation,
        radius_km: Decimal
    ) -> List[VehicleEntity]:
        """Obtener vehículos cerca de una ubicación."""
        pass

    @abstractmethod
    async def track_vehicle_route(
        self,
        vehicle_id: UUID,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[GPSLocation]:
        """Obtener ruta histórica de un vehículo."""
        pass


class VehicleMaintenanceServiceInterface(ABC):
    """Interface para el servicio de mantenimiento de vehículos."""

    @abstractmethod
    async def schedule_maintenance(
        self,
        vehicle_id: UUID,
        maintenance_type: str,
        scheduled_date: str,
        description: Optional[str] = None
    ) -> bool:
        """Programar mantenimiento para un vehículo."""
        pass

    @abstractmethod
    async def complete_maintenance(
        self,
        vehicle_id: UUID,
        maintenance_data: dict
    ) -> bool:
        """Completar mantenimiento de un vehículo."""
        pass

    @abstractmethod
    async def get_maintenance_history(
        self,
        vehicle_id: UUID
    ) -> List[dict]:
        """Obtener historial de mantenimiento de un vehículo."""
        pass


class VehicleAnalyticsServiceInterface(ABC):
    """Interface para el servicio de análisis de vehículos."""

    @abstractmethod
    async def get_vehicle_utilization_stats(
        self,
        vehicle_id: Optional[UUID] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """Obtener estadísticas de utilización de vehículos."""
        pass

    @abstractmethod
    async def get_fleet_performance_metrics(
        self,
        owner_id: Optional[UUID] = None
    ) -> dict:
        """Obtener métricas de rendimiento de la flota."""
        pass

    @abstractmethod
    async def get_maintenance_cost_analysis(
        self,
        vehicle_id: Optional[UUID] = None,
        period_months: int = 12
    ) -> dict:
        """Obtener análisis de costos de mantenimiento."""
        pass


class VehicleEventServiceInterface(ABC):
    """Interface para el servicio de eventos de vehículos."""

    @abstractmethod
    async def publish_vehicle_status_changed(
        self,
        vehicle_id: UUID,
        old_status: VehicleStatus,
        new_status: VehicleStatus
    ) -> None:
        """Publicar evento de cambio de estado de vehículo."""
        pass

    @abstractmethod
    async def publish_vehicle_location_updated(
        self,
        vehicle_id: UUID,
        location: GPSLocation
    ) -> None:
        """Publicar evento de actualización de ubicación."""
        pass

    @abstractmethod
    async def publish_maintenance_due(
        self,
        vehicle_id: UUID,
        maintenance_type: str
    ) -> None:
        """Publicar evento de mantenimiento debido."""
        pass
