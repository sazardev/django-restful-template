"""
Vehicle Application Services.
Servicios de la capa de aplicación para vehículos.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from apps.vehicles.domain.entities import (
    VehicleEntity, VehicleSpecifications, GPSLocation, MaintenanceRecord,
    VehicleType, VehicleStatus, FuelType
)
from apps.vehicles.domain.interfaces import (
    VehicleRepositoryInterface,
    VehicleLocationServiceInterface,
    VehicleMaintenanceServiceInterface,
    VehicleAnalyticsServiceInterface,
    VehicleEventServiceInterface
)
from apps.vehicles.domain.exceptions import (
    VehicleNotFound, VehicleAlreadyExists, VehicleNotAvailable,
    InvalidVehicleOperation, InvalidLocationData
)
from shared.domain.exceptions import ValidationError
from .dtos import (
    VehicleCreateDTO, VehicleUpdateDTO, VehicleResponseDTO,
    VehicleListResponseDTO, VehicleFilterDTO, VehicleLocationUpdateDTO,
    VehicleAssignmentDTO, VehicleMaintenanceDTO, VehicleAnalyticsDTO,
    FleetSummaryDTO, VehicleUtilizationDTO, VehicleSearchDTO,
    GPSLocationDTO, MaintenanceRecordDTO, VehicleSpecificationsDTO
)

logger = logging.getLogger(__name__)


class VehicleService:
    """Servicio principal para gestión de vehículos."""

    def __init__(
        self,
        vehicle_repository: VehicleRepositoryInterface,
        event_service: VehicleEventServiceInterface
    ):
        self.vehicle_repository = vehicle_repository
        self.event_service = event_service

    async def create_vehicle(self, vehicle_data: VehicleCreateDTO) -> VehicleResponseDTO:
        """Crear un nuevo vehículo."""
        logger.info(f"Creando vehículo con placa: {vehicle_data.license_plate}")

        # Validar que no exista un vehículo con la misma placa
        existing_vehicle = await self.vehicle_repository.get_by_license_plate(
            vehicle_data.license_plate
        )
        if existing_vehicle:
            raise VehicleAlreadyExists(vehicle_data.license_plate)

        # Validar datos
        self._validate_vehicle_data(vehicle_data)

        # Crear entidad de dominio
        vehicle_entity = self._create_vehicle_entity(vehicle_data)

        # Guardar en repositorio
        created_vehicle = await self.vehicle_repository.create(vehicle_entity)

        # Publicar evento
        await self.event_service.publish_vehicle_status_changed(
            created_vehicle.id,
            None,
            created_vehicle.status
        )

        logger.info(f"Vehículo creado exitosamente: {created_vehicle.id}")
        return self._entity_to_response_dto(created_vehicle)

    async def get_vehicle_by_id(self, vehicle_id: UUID) -> VehicleResponseDTO:
        """Obtener vehículo por ID."""
        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(vehicle_id))
        
        return self._entity_to_response_dto(vehicle)

    async def get_vehicles(
        self,
        filters: Optional[VehicleFilterDTO] = None,
        page: int = 1,
        page_size: int = 20
    ) -> VehicleListResponseDTO:
        """Obtener lista de vehículos con filtros y paginación."""
        skip = (page - 1) * page_size
        
        filter_dict = self._build_filter_dict(filters) if filters else {}
        
        vehicles = await self.vehicle_repository.get_all(
            skip=skip,
            limit=page_size,
            filters=filter_dict
        )
        
        total_count = await self.vehicle_repository.count(filter_dict)
        total_pages = (total_count + page_size - 1) // page_size

        vehicle_dtos = [self._entity_to_response_dto(v) for v in vehicles]

        return VehicleListResponseDTO(
            vehicles=vehicle_dtos,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def update_vehicle(
        self,
        vehicle_id: UUID,
        update_data: VehicleUpdateDTO
    ) -> VehicleResponseDTO:
        """Actualizar vehículo."""
        logger.info(f"Actualizando vehículo: {vehicle_id}")

        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(vehicle_id))

        old_status = vehicle.status

        # Aplicar actualizaciones
        self._apply_updates_to_entity(vehicle, update_data)

        # Guardar cambios
        updated_vehicle = await self.vehicle_repository.update(vehicle)

        # Publicar evento si cambió el estado
        if old_status != updated_vehicle.status:
            await self.event_service.publish_vehicle_status_changed(
                vehicle_id, old_status, updated_vehicle.status
            )

        logger.info(f"Vehículo actualizado: {vehicle_id}")
        return self._entity_to_response_dto(updated_vehicle)

    async def delete_vehicle(self, vehicle_id: UUID) -> bool:
        """Eliminar vehículo."""
        logger.info(f"Eliminando vehículo: {vehicle_id}")

        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(vehicle_id))

        if vehicle.status == VehicleStatus.IN_USE:
            raise InvalidVehicleOperation(
                "No se puede eliminar un vehículo que está en uso"
            )

        result = await self.vehicle_repository.delete(vehicle_id)
        
        if result:
            logger.info(f"Vehículo eliminado: {vehicle_id}")
        
        return result

    async def assign_driver(self, assignment: VehicleAssignmentDTO) -> VehicleResponseDTO:
        """Asignar conductor a vehículo."""
        vehicle = await self.vehicle_repository.get_by_id(assignment.vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(assignment.vehicle_id))

        vehicle.assign_driver(assignment.driver_id)
        updated_vehicle = await self.vehicle_repository.update(vehicle)

        await self.event_service.publish_vehicle_status_changed(
            assignment.vehicle_id, VehicleStatus.AVAILABLE, VehicleStatus.IN_USE
        )

        return self._entity_to_response_dto(updated_vehicle)

    async def unassign_driver(self, vehicle_id: UUID) -> VehicleResponseDTO:
        """Desasignar conductor de vehículo."""
        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(vehicle_id))

        vehicle.unassign_driver()
        updated_vehicle = await self.vehicle_repository.update(vehicle)

        await self.event_service.publish_vehicle_status_changed(
            vehicle_id, VehicleStatus.IN_USE, VehicleStatus.AVAILABLE
        )

        return self._entity_to_response_dto(updated_vehicle)

    async def get_available_vehicles(
        self,
        vehicle_type: Optional[str] = None,
        min_weight_capacity: Optional[Decimal] = None,
        min_volume_capacity: Optional[Decimal] = None
    ) -> List[VehicleResponseDTO]:
        """Obtener vehículos disponibles."""
        vehicle_type_enum = VehicleType(vehicle_type) if vehicle_type else None
        
        vehicles = await self.vehicle_repository.get_available_vehicles(
            vehicle_type=vehicle_type_enum,
            min_weight_capacity=min_weight_capacity,
            min_volume_capacity=min_volume_capacity
        )

        return [self._entity_to_response_dto(v) for v in vehicles]

    def _validate_vehicle_data(self, vehicle_data: VehicleCreateDTO) -> None:
        """Validar datos del vehículo."""
        if not vehicle_data.license_plate.strip():
            raise ValidationError("La placa es obligatoria")
        
        if vehicle_data.year < 1900 or vehicle_data.year > datetime.now().year + 1:
            raise ValidationError("Año de vehículo inválido")
        
        if vehicle_data.specifications.max_weight_kg <= 0:
            raise ValidationError("Peso máximo debe ser mayor a 0")
        
        if vehicle_data.specifications.max_volume_m3 <= 0:
            raise ValidationError("Volumen máximo debe ser mayor a 0")

    def _create_vehicle_entity(self, vehicle_data: VehicleCreateDTO) -> VehicleEntity:
        """Crear entidad de vehículo desde DTO."""
        specifications = VehicleSpecifications(
            max_weight_kg=vehicle_data.specifications.max_weight_kg,
            max_volume_m3=vehicle_data.specifications.max_volume_m3,
            fuel_type=FuelType(vehicle_data.specifications.fuel_type),
            fuel_capacity_liters=vehicle_data.specifications.fuel_capacity_liters,
            engine_power_hp=vehicle_data.specifications.engine_power_hp,
            transmission_type=vehicle_data.specifications.transmission_type,
            emissions_standard=vehicle_data.specifications.emissions_standard
        )

        current_location = None
        if vehicle_data.current_location:
            current_location = GPSLocation(
                latitude=vehicle_data.current_location.latitude,
                longitude=vehicle_data.current_location.longitude,
                accuracy_meters=vehicle_data.current_location.accuracy_meters,
                altitude_meters=vehicle_data.current_location.altitude_meters,
                timestamp=vehicle_data.current_location.timestamp
            )

        now = datetime.now()
        return VehicleEntity(
            id=uuid4(),
            license_plate=vehicle_data.license_plate,
            brand=vehicle_data.brand,
            model=vehicle_data.model,
            year=vehicle_data.year,
            color=vehicle_data.color,
            vehicle_type=VehicleType(vehicle_data.vehicle_type),
            specifications=specifications,
            status=VehicleStatus.AVAILABLE,
            current_location=current_location,
            current_driver_id=None,
            owner_id=vehicle_data.owner_id,
            vin_number=vehicle_data.vin_number,
            registration_expiry=vehicle_data.registration_expiry,
            insurance_expiry=vehicle_data.insurance_expiry,
            created_at=now,
            updated_at=now
        )

    def _apply_updates_to_entity(
        self,
        vehicle: VehicleEntity,
        update_data: VehicleUpdateDTO
    ) -> None:
        """Aplicar actualizaciones a la entidad."""
        if update_data.color:
            vehicle.color = update_data.color
        
        if update_data.status:
            vehicle.status = VehicleStatus(update_data.status)
        
        if update_data.registration_expiry:
            vehicle.registration_expiry = update_data.registration_expiry
        
        if update_data.insurance_expiry:
            vehicle.insurance_expiry = update_data.insurance_expiry
        
        if update_data.total_mileage_km:
            vehicle.update_mileage(update_data.total_mileage_km)
        
        if update_data.current_location:
            location = GPSLocation(
                latitude=update_data.current_location.latitude,
                longitude=update_data.current_location.longitude,
                accuracy_meters=update_data.current_location.accuracy_meters,
                altitude_meters=update_data.current_location.altitude_meters,
                timestamp=update_data.current_location.timestamp or datetime.now()
            )
            vehicle.update_location(location)
        
        vehicle.updated_at = datetime.now()

    def _entity_to_response_dto(self, vehicle: VehicleEntity) -> VehicleResponseDTO:
        """Convertir entidad a DTO de respuesta."""
        current_location = None
        if vehicle.current_location:
            current_location = GPSLocationDTO(
                latitude=vehicle.current_location.latitude,
                longitude=vehicle.current_location.longitude,
                accuracy_meters=vehicle.current_location.accuracy_meters,
                altitude_meters=vehicle.current_location.altitude_meters,
                timestamp=vehicle.current_location.timestamp
            )

        specifications = VehicleSpecificationsDTO(
            max_weight_kg=vehicle.specifications.max_weight_kg,
            max_volume_m3=vehicle.specifications.max_volume_m3,
            fuel_type=vehicle.specifications.fuel_type.value,
            fuel_capacity_liters=vehicle.specifications.fuel_capacity_liters,
            engine_power_hp=vehicle.specifications.engine_power_hp,
            transmission_type=vehicle.specifications.transmission_type,
            emissions_standard=vehicle.specifications.emissions_standard
        )

        maintenance_records = [
            MaintenanceRecordDTO(
                id=record.id,
                vehicle_id=record.vehicle_id,
                maintenance_type=record.maintenance_type,
                description=record.description,
                cost=record.cost,
                performed_at=record.performed_at,
                next_maintenance_date=record.next_maintenance_date,
                mileage_km=record.mileage_km,
                performed_by=record.performed_by,
                notes=record.notes
            )
            for record in vehicle.maintenance_records
        ]

        # Calcular campos derivados
        days_until_registration_expiry = None
        if vehicle.registration_expiry:
            delta = vehicle.registration_expiry - datetime.now()
            days_until_registration_expiry = delta.days

        days_until_insurance_expiry = None
        if vehicle.insurance_expiry:
            delta = vehicle.insurance_expiry - datetime.now()
            days_until_insurance_expiry = delta.days

        return VehicleResponseDTO(
            id=vehicle.id,
            license_plate=vehicle.license_plate,
            brand=vehicle.brand,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            vehicle_type=vehicle.vehicle_type.value,
            specifications=specifications,
            status=vehicle.status.value,
            current_location=current_location,
            current_driver_id=vehicle.current_driver_id,
            owner_id=vehicle.owner_id,
            vin_number=vehicle.vin_number,
            registration_expiry=vehicle.registration_expiry,
            insurance_expiry=vehicle.insurance_expiry,
            last_maintenance_date=vehicle.last_maintenance_date,
            total_mileage_km=vehicle.total_mileage_km,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
            maintenance_records=maintenance_records,
            is_maintenance_due=vehicle.is_maintenance_due(),
            is_available_for_route=vehicle.is_available_for_route(),
            days_until_registration_expiry=days_until_registration_expiry,
            days_until_insurance_expiry=days_until_insurance_expiry
        )

    def _build_filter_dict(self, filters: VehicleFilterDTO) -> Dict[str, Any]:
        """Construir diccionario de filtros."""
        filter_dict = {}
        
        if filters.vehicle_type:
            filter_dict['vehicle_type'] = filters.vehicle_type
        if filters.status:
            filter_dict['status'] = filters.status
        if filters.owner_id:
            filter_dict['owner_id'] = filters.owner_id
        if filters.brand:
            filter_dict['brand'] = filters.brand
        if filters.model:
            filter_dict['model'] = filters.model
        if filters.year_from:
            filter_dict['year_from'] = filters.year_from
        if filters.year_to:
            filter_dict['year_to'] = filters.year_to
        if filters.available_only:
            filter_dict['available_only'] = filters.available_only
        if filters.maintenance_due:
            filter_dict['maintenance_due'] = filters.maintenance_due
        
        return filter_dict


class VehicleLocationService:
    """Servicio para gestión de ubicación de vehículos."""

    def __init__(
        self,
        vehicle_repository: VehicleRepositoryInterface,
        location_service: VehicleLocationServiceInterface,
        event_service: VehicleEventServiceInterface
    ):
        self.vehicle_repository = vehicle_repository
        self.location_service = location_service
        self.event_service = event_service

    async def update_vehicle_location(
        self,
        update_data: VehicleLocationUpdateDTO
    ) -> bool:
        """Actualizar ubicación de vehículo."""
        # Validar que el vehículo existe
        vehicle = await self.vehicle_repository.get_by_id(update_data.vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(update_data.vehicle_id))

        # Crear objeto de ubicación
        location = GPSLocation(
            latitude=update_data.location.latitude,
            longitude=update_data.location.longitude,
            accuracy_meters=update_data.location.accuracy_meters,
            altitude_meters=update_data.location.altitude_meters,
            timestamp=update_data.location.timestamp or datetime.now()
        )

        # Actualizar ubicación en el vehículo
        vehicle.update_location(location)
        await self.vehicle_repository.update(vehicle)

        # Actualizar en el servicio de ubicación
        result = await self.location_service.update_vehicle_location(
            update_data.vehicle_id, location
        )

        if result:
            # Publicar evento
            await self.event_service.publish_vehicle_location_updated(
                update_data.vehicle_id, location
            )

        return result


class VehicleMaintenanceService:
    """Servicio para gestión de mantenimiento de vehículos."""

    def __init__(
        self,
        vehicle_repository: VehicleRepositoryInterface,
        maintenance_service: VehicleMaintenanceServiceInterface,
        event_service: VehicleEventServiceInterface
    ):
        self.vehicle_repository = vehicle_repository
        self.maintenance_service = maintenance_service
        self.event_service = event_service

    async def schedule_maintenance(
        self,
        maintenance_data: VehicleMaintenanceDTO
    ) -> bool:
        """Programar mantenimiento."""
        vehicle = await self.vehicle_repository.get_by_id(maintenance_data.vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(maintenance_data.vehicle_id))

        # Programar en el servicio externo
        result = await self.maintenance_service.schedule_maintenance(
            maintenance_data.vehicle_id,
            maintenance_data.maintenance_type,
            maintenance_data.scheduled_date.isoformat() if maintenance_data.scheduled_date else "",
            maintenance_data.description
        )

        if result:
            # Cambiar estado a mantenimiento si es necesario
            if maintenance_data.performed_at:  # Mantenimiento inmediato
                vehicle.start_maintenance()
                await self.vehicle_repository.update(vehicle)

        return result

    async def complete_maintenance(
        self,
        maintenance_data: VehicleMaintenanceDTO
    ) -> bool:
        """Completar mantenimiento."""
        vehicle = await self.vehicle_repository.get_by_id(maintenance_data.vehicle_id)
        if not vehicle:
            raise VehicleNotFound(str(maintenance_data.vehicle_id))

        # Crear registro de mantenimiento
        maintenance_record = MaintenanceRecord(
            id=uuid4(),
            vehicle_id=maintenance_data.vehicle_id,
            maintenance_type=maintenance_data.maintenance_type,
            description=maintenance_data.description,
            cost=maintenance_data.cost,
            performed_at=maintenance_data.performed_at or datetime.now(),
            next_maintenance_date=maintenance_data.scheduled_date,
            mileage_km=maintenance_data.mileage_km,
            performed_by=maintenance_data.performed_by,
            notes=maintenance_data.notes
        )

        # Completar mantenimiento en el vehículo
        vehicle.finish_maintenance(maintenance_record)
        await self.vehicle_repository.update(vehicle)

        # Completar en el servicio externo
        maintenance_dict = {
            'maintenance_type': maintenance_data.maintenance_type,
            'description': maintenance_data.description,
            'cost': float(maintenance_data.cost),
            'performed_at': maintenance_data.performed_at.isoformat() if maintenance_data.performed_at else "",
            'mileage_km': float(maintenance_data.mileage_km) if maintenance_data.mileage_km else None,
            'performed_by': maintenance_data.performed_by,
            'notes': maintenance_data.notes
        }

        result = await self.maintenance_service.complete_maintenance(
            maintenance_data.vehicle_id, maintenance_dict
        )

        return result


class VehicleAnalyticsService:
    """Servicio para análisis de vehículos."""

    def __init__(
        self,
        vehicle_repository: VehicleRepositoryInterface,
        analytics_service: VehicleAnalyticsServiceInterface
    ):
        self.vehicle_repository = vehicle_repository
        self.analytics_service = analytics_service

    async def get_fleet_summary(self, owner_id: Optional[UUID] = None) -> FleetSummaryDTO:
        """Obtener resumen de la flota."""
        # Obtener métricas básicas
        if owner_id:
            vehicles = await self.vehicle_repository.get_by_owner(owner_id)
        else:
            vehicles = await self.vehicle_repository.get_all()

        total_vehicles = len(vehicles)
        active_vehicles = len([v for v in vehicles if v.status != VehicleStatus.RETIRED])
        in_maintenance = len([v for v in vehicles if v.status == VehicleStatus.MAINTENANCE])
        available_vehicles = len([v for v in vehicles if v.status == VehicleStatus.AVAILABLE])

        # Calcular capacidades totales
        total_weight = sum(v.specifications.max_weight_kg for v in vehicles)
        total_volume = sum(v.specifications.max_volume_m3 for v in vehicles)

        # Calcular edad promedio
        current_year = datetime.now().year
        average_age = sum(current_year - v.year for v in vehicles) / total_vehicles if total_vehicles > 0 else 0

        # Obtener métricas avanzadas del servicio
        performance_metrics = await self.analytics_service.get_fleet_performance_metrics(owner_id)
        utilization_rate = Decimal(str(performance_metrics.get('utilization_rate', 0)))

        return FleetSummaryDTO(
            total_vehicles=total_vehicles,
            active_vehicles=active_vehicles,
            in_maintenance=in_maintenance,
            available_vehicles=available_vehicles,
            average_age_years=Decimal(str(average_age)),
            total_capacity_weight_kg=total_weight,
            total_capacity_volume_m3=total_volume,
            utilization_rate=utilization_rate,
            maintenance_cost_trend=performance_metrics.get('maintenance_cost_trend', {})
        )

# Compatibility alias
VehicleApplicationService = VehicleService
