"""
Vehicle DTOs (Data Transfer Objects).
DTOs para transferencia de datos del sistema de vehículos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from apps.vehicles.domain.entities import VehicleType, VehicleStatus, FuelType


@dataclass
class VehicleSpecificationsDTO:
    """DTO para especificaciones de vehículo."""
    max_weight_kg: Decimal
    max_volume_m3: Decimal
    fuel_type: str
    fuel_capacity_liters: Optional[Decimal] = None
    engine_power_hp: Optional[int] = None
    transmission_type: Optional[str] = None
    emissions_standard: Optional[str] = None


@dataclass
class GPSLocationDTO:
    """DTO para ubicación GPS."""
    latitude: Decimal
    longitude: Decimal
    accuracy_meters: Optional[Decimal] = None
    altitude_meters: Optional[Decimal] = None
    timestamp: Optional[datetime] = None


@dataclass
class MaintenanceRecordDTO:
    """DTO para registro de mantenimiento."""
    id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    maintenance_type: str = ""
    description: str = ""
    cost: Decimal = Decimal('0')
    performed_at: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    mileage_km: Optional[Decimal] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class VehicleCreateDTO:
    """DTO para crear un vehículo."""
    license_plate: str
    brand: str
    model: str
    year: int
    color: str
    vehicle_type: str
    specifications: VehicleSpecificationsDTO
    owner_id: UUID
    vin_number: Optional[str] = None
    registration_expiry: Optional[datetime] = None
    insurance_expiry: Optional[datetime] = None
    current_location: Optional[GPSLocationDTO] = None


@dataclass
class VehicleUpdateDTO:
    """DTO para actualizar un vehículo."""
    color: Optional[str] = None
    specifications: Optional[VehicleSpecificationsDTO] = None
    status: Optional[str] = None
    current_location: Optional[GPSLocationDTO] = None
    registration_expiry: Optional[datetime] = None
    insurance_expiry: Optional[datetime] = None
    total_mileage_km: Optional[Decimal] = None


@dataclass
class VehicleResponseDTO:
    """DTO para respuesta de vehículo."""
    id: UUID
    license_plate: str
    brand: str
    model: str
    year: int
    color: str
    vehicle_type: str
    specifications: VehicleSpecificationsDTO
    status: str
    current_location: Optional[GPSLocationDTO]
    current_driver_id: Optional[UUID]
    owner_id: UUID
    vin_number: Optional[str]
    registration_expiry: Optional[datetime]
    insurance_expiry: Optional[datetime]
    last_maintenance_date: Optional[datetime]
    total_mileage_km: Decimal
    created_at: datetime
    updated_at: datetime
    maintenance_records: List[MaintenanceRecordDTO] = field(default_factory=list)
    
    # Campos calculados
    is_maintenance_due: bool = False
    is_available_for_route: bool = False
    days_until_registration_expiry: Optional[int] = None
    days_until_insurance_expiry: Optional[int] = None


@dataclass
class VehicleListResponseDTO:
    """DTO para lista de vehículos."""
    vehicles: List[VehicleResponseDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int


@dataclass
class VehicleFilterDTO:
    """DTO para filtros de vehículos."""
    vehicle_type: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[UUID] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    min_weight_capacity: Optional[Decimal] = None
    max_weight_capacity: Optional[Decimal] = None
    min_volume_capacity: Optional[Decimal] = None
    max_volume_capacity: Optional[Decimal] = None
    fuel_type: Optional[str] = None
    maintenance_due: Optional[bool] = None
    available_only: Optional[bool] = None
    near_location: Optional[GPSLocationDTO] = None
    radius_km: Optional[Decimal] = None
    current_driver_id: Optional[UUID] = None
    registration_expiring_days: Optional[int] = None
    insurance_expiring_days: Optional[int] = None


@dataclass
class VehicleLocationUpdateDTO:
    """DTO para actualización de ubicación."""
    vehicle_id: UUID
    location: GPSLocationDTO


@dataclass
class VehicleAssignmentDTO:
    """DTO para asignación de conductor."""
    vehicle_id: UUID
    driver_id: UUID


@dataclass
class VehicleMaintenanceDTO:
    """DTO para mantenimiento de vehículo."""
    vehicle_id: UUID
    maintenance_type: str
    description: str
    cost: Decimal
    scheduled_date: Optional[datetime] = None
    performed_at: Optional[datetime] = None
    mileage_km: Optional[Decimal] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class VehicleAnalyticsDTO:
    """DTO para análisis de vehículos."""
    vehicle_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VehicleUtilizationDTO:
    """DTO para utilización de vehículo."""
    vehicle_id: UUID
    utilization_percent: Decimal
    active_hours: Decimal
    total_distance_km: Decimal
    fuel_consumption: Optional[Decimal] = None
    maintenance_costs: Decimal = Decimal('0')
    revenue_generated: Optional[Decimal] = None


@dataclass
class FleetSummaryDTO:
    """DTO para resumen de flota."""
    total_vehicles: int
    active_vehicles: int
    in_maintenance: int
    available_vehicles: int
    average_age_years: Decimal
    total_capacity_weight_kg: Decimal
    total_capacity_volume_m3: Decimal
    utilization_rate: Decimal
    maintenance_cost_trend: Dict[str, Decimal] = field(default_factory=dict)


@dataclass
class VehicleSearchDTO:
    """DTO para búsqueda de vehículos."""
    query: str
    filters: Optional[VehicleFilterDTO] = None
    sort_by: Optional[str] = None
    sort_direction: str = "asc"
    include_inactive: bool = False
