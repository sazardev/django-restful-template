"""
Vehicle Domain Models.
Entidades de dominio para el sistema de vehículos.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal


class VehicleType(Enum):
    """Tipos de vehículos."""
    TRUCK = "truck"
    VAN = "van"
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    TRAILER = "trailer"
    CONTAINER = "container"


class VehicleStatus(Enum):
    """Estados de vehículos."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


class FuelType(Enum):
    """Tipos de combustible."""
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    CNG = "cng"  # Compressed Natural Gas
    LPG = "lpg"  # Liquefied Petroleum Gas


@dataclass(frozen=True)
class VehicleSpecifications:
    """Especificaciones técnicas del vehículo - Value Object."""
    max_weight_kg: Decimal
    max_volume_m3: Decimal
    fuel_type: FuelType
    fuel_capacity_liters: Optional[Decimal] = None
    engine_power_hp: Optional[int] = None
    transmission_type: Optional[str] = None
    emissions_standard: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        if self.max_weight_kg <= 0:
            raise ValueError("El peso máximo debe ser mayor a 0")
        if self.max_volume_m3 <= 0:
            raise ValueError("El volumen máximo debe ser mayor a 0")


@dataclass(frozen=True)
class GPSLocation:
    """Ubicación GPS - Value Object."""
    latitude: Decimal
    longitude: Decimal
    accuracy_meters: Optional[Decimal] = None
    altitude_meters: Optional[Decimal] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de coordenadas GPS."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError("Latitud debe estar entre -90 y 90")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("Longitud debe estar entre -180 y 180")
    
    def distance_to(self, other: 'GPSLocation') -> Decimal:
        """Calcular distancia a otra ubicación usando fórmula de Haversine."""
        import math
        
        # Convertir a radianes
        lat1_rad = math.radians(float(self.latitude))
        lon1_rad = math.radians(float(self.longitude))
        lat2_rad = math.radians(float(other.latitude))
        lon2_rad = math.radians(float(other.longitude))
        
        # Diferencias
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Fórmula de Haversine
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Radio de la Tierra en kilómetros
        radius_km = 6371
        
        return Decimal(str(c * radius_km))


@dataclass
class MaintenanceRecord:
    """Registro de mantenimiento."""
    id: UUID
    vehicle_id: UUID
    maintenance_type: str
    description: str
    cost: Decimal
    performed_at: datetime
    next_maintenance_date: Optional[datetime]
    mileage_km: Optional[Decimal]
    performed_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class VehicleEntity:
    """Entidad de vehículo del dominio."""
    id: UUID
    license_plate: str
    brand: str
    model: str
    year: int
    color: str
    vehicle_type: VehicleType
    specifications: VehicleSpecifications
    status: VehicleStatus
    current_location: Optional[GPSLocation]
    current_driver_id: Optional[UUID]
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    vin_number: Optional[str] = None
    registration_expiry: Optional[datetime] = None
    insurance_expiry: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    total_mileage_km: Decimal = Decimal('0')
    maintenance_records: List[MaintenanceRecord] = None
    
    def __post_init__(self):
        if self.maintenance_records is None:
            self.maintenance_records = []
    
    def update_location(self, new_location: GPSLocation) -> None:
        """Actualizar ubicación del vehículo."""
        if self.status not in [VehicleStatus.AVAILABLE, VehicleStatus.IN_USE]:
            raise ValueError(f"No se puede actualizar ubicación: vehículo está {self.status.value}")
        
        self.current_location = new_location
        self.updated_at = datetime.now()
    
    def assign_driver(self, driver_id: UUID) -> None:
        """Asignar conductor al vehículo."""
        if self.status != VehicleStatus.AVAILABLE:
            raise ValueError(f"Vehículo no disponible para asignación: {self.status.value}")
        
        self.current_driver_id = driver_id
        self.status = VehicleStatus.IN_USE
        self.updated_at = datetime.now()
    
    def unassign_driver(self) -> None:
        """Desasignar conductor del vehículo."""
        self.current_driver_id = None
        self.status = VehicleStatus.AVAILABLE
        self.updated_at = datetime.now()
    
    def start_maintenance(self) -> None:
        """Iniciar mantenimiento del vehículo."""
        if self.status == VehicleStatus.IN_USE and self.current_driver_id:
            raise ValueError("No se puede poner en mantenimiento: vehículo en uso")
        
        self.status = VehicleStatus.MAINTENANCE
        self.current_driver_id = None
        self.updated_at = datetime.now()
    
    def finish_maintenance(self, maintenance_record: MaintenanceRecord) -> None:
        """Finalizar mantenimiento del vehículo."""
        if self.status != VehicleStatus.MAINTENANCE:
            raise ValueError("Vehículo no está en mantenimiento")
        
        self.maintenance_records.append(maintenance_record)
        self.last_maintenance_date = maintenance_record.performed_at
        self.status = VehicleStatus.AVAILABLE
        self.updated_at = datetime.now()
    
    def retire_vehicle(self) -> None:
        """Retirar vehículo del servicio."""
        if self.status == VehicleStatus.IN_USE:
            raise ValueError("No se puede retirar: vehículo en uso")
        
        self.status = VehicleStatus.RETIRED
        self.current_driver_id = None
        self.updated_at = datetime.now()
    
    def update_mileage(self, new_mileage: Decimal) -> None:
        """Actualizar kilometraje del vehículo."""
        if new_mileage < self.total_mileage_km:
            raise ValueError("El nuevo kilometraje no puede ser menor al actual")
        
        self.total_mileage_km = new_mileage
        self.updated_at = datetime.now()
    
    def is_maintenance_due(self) -> bool:
        """Verificar si el vehículo necesita mantenimiento."""
        if not self.last_maintenance_date:
            return True  # Nunca ha tenido mantenimiento
        
        # Verificar por fecha (6 meses)
        from datetime import timedelta
        maintenance_interval = timedelta(days=180)
        if datetime.now() - self.last_maintenance_date > maintenance_interval:
            return True
        
        # Verificar por kilometraje (cada 10,000 km)
        if self.maintenance_records:
            last_maintenance = max(
                self.maintenance_records, 
                key=lambda r: r.performed_at
            )
            if (self.total_mileage_km - 
                (last_maintenance.mileage_km or Decimal('0'))) > Decimal('10000'):
                return True
        
        return False
    
    def can_carry_weight(self, weight_kg: Decimal) -> bool:
        """Verificar si el vehículo puede cargar cierto peso."""
        return weight_kg <= self.specifications.max_weight_kg
    
    def can_carry_volume(self, volume_m3: Decimal) -> bool:
        """Verificar si el vehículo puede cargar cierto volumen."""
        return volume_m3 <= self.specifications.max_volume_m3
    
    def is_available_for_route(self) -> bool:
        """Verificar si el vehículo está disponible para una ruta."""
        return (
            self.status == VehicleStatus.AVAILABLE and
            not self.is_maintenance_due() and
            self.registration_expiry and self.registration_expiry > datetime.now() and
            self.insurance_expiry and self.insurance_expiry > datetime.now()
        )
    
    def get_capacity_utilization(self, current_weight: Decimal, current_volume: Decimal) -> Dict[str, Decimal]:
        """Obtener porcentaje de utilización de capacidad."""
        weight_utilization = (current_weight / self.specifications.max_weight_kg) * 100
        volume_utilization = (current_volume / self.specifications.max_volume_m3) * 100
        
        return {
            'weight_utilization_percent': min(weight_utilization, Decimal('100')),
            'volume_utilization_percent': min(volume_utilization, Decimal('100')),
            'overall_utilization_percent': max(weight_utilization, volume_utilization)
        }
