"""
Vehicle Repository Implementation.
Implementación del repositorio de vehículos.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from django.db.models import Q, F, Count, Avg
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import sync_to_async

from apps.vehicles.domain.entities import (
    VehicleEntity, VehicleSpecifications, GPSLocation, MaintenanceRecord,
    VehicleType, VehicleStatus, FuelType
)
from apps.vehicles.domain.interfaces import VehicleRepositoryInterface
from apps.vehicles.domain.exceptions import VehicleNotFound
from .models import Vehicle, VehicleLocation, MaintenanceRecord as MaintenanceRecordModel

logger = logging.getLogger(__name__)


class VehicleRepository(VehicleRepositoryInterface):
    """Implementación del repositorio de vehículos usando Django ORM."""

    async def create(self, vehicle: VehicleEntity) -> VehicleEntity:
        """Crear un nuevo vehículo."""
        try:
            vehicle_model = Vehicle(
                id=vehicle.id,
                license_plate=vehicle.license_plate,
                brand=vehicle.brand,
                model=vehicle.model,
                year=vehicle.year,
                color=vehicle.color,
                vehicle_type=vehicle.vehicle_type.value,
                vin_number=vehicle.vin_number,
                status=vehicle.status.value,
                current_driver_id=vehicle.current_driver_id,
                owner_id=vehicle.owner_id,
                max_weight_kg=vehicle.specifications.max_weight_kg,
                max_volume_m3=vehicle.specifications.max_volume_m3,
                fuel_type=vehicle.specifications.fuel_type.value,
                fuel_capacity_liters=vehicle.specifications.fuel_capacity_liters,
                engine_power_hp=vehicle.specifications.engine_power_hp,
                transmission_type=vehicle.specifications.transmission_type,
                emissions_standard=vehicle.specifications.emissions_standard,
                registration_expiry=vehicle.registration_expiry,
                insurance_expiry=vehicle.insurance_expiry,
                total_mileage_km=vehicle.total_mileage_km,
                last_maintenance_date=vehicle.last_maintenance_date,
                created_at=vehicle.created_at,
                updated_at=vehicle.updated_at
            )
            
            await sync_to_async(vehicle_model.save)()
            
            # Crear ubicación inicial si existe
            if vehicle.current_location:
                await self._create_vehicle_location(vehicle.id, vehicle.current_location)
            
            # Crear registros de mantenimiento si existen
            for maintenance in vehicle.maintenance_records:
                await self._create_maintenance_record(maintenance)
            
            logger.info(f"Vehículo creado: {vehicle.id}")
            return vehicle
            
        except Exception as e:
            logger.error(f"Error creando vehículo: {e}")
            raise

    async def get_by_id(self, vehicle_id: UUID) -> Optional[VehicleEntity]:
        """Obtener vehículo por ID."""
        try:
            vehicle_model = await sync_to_async(
                Vehicle.objects.select_related('current_driver', 'owner').get
            )(id=vehicle_id)
            
            return await self._model_to_entity(vehicle_model)
            
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo vehículo {vehicle_id}: {e}")
            raise

    async def get_by_license_plate(self, license_plate: str) -> Optional[VehicleEntity]:
        """Obtener vehículo por placa."""
        try:
            vehicle_model = await sync_to_async(
                Vehicle.objects.select_related('current_driver', 'owner').get
            )(license_plate=license_plate.upper())
            
            return await self._model_to_entity(vehicle_model)
            
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo vehículo por placa {license_plate}: {e}")
            raise

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[VehicleEntity]:
        """Obtener lista de vehículos con filtros opcionales."""
        try:
            queryset = Vehicle.objects.select_related('current_driver', 'owner')
            
            if filters:
                queryset = self._apply_filters(queryset, filters)
            
            vehicles_models = await sync_to_async(list)(
                queryset[skip:skip + limit]
            )
            
            entities = []
            for vehicle_model in vehicles_models:
                entity = await self._model_to_entity(vehicle_model)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error obteniendo vehículos: {e}")
            raise

    async def get_by_owner(self, owner_id: UUID) -> List[VehicleEntity]:
        """Obtener vehículos por propietario."""
        try:
            vehicles_models = await sync_to_async(list)(
                Vehicle.objects.select_related('current_driver', 'owner')
                .filter(owner_id=owner_id, is_active=True)
            )
            
            entities = []
            for vehicle_model in vehicles_models:
                entity = await self._model_to_entity(vehicle_model)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error obteniendo vehículos del propietario {owner_id}: {e}")
            raise

    async def get_available_vehicles(
        self,
        vehicle_type: Optional[VehicleType] = None,
        min_weight_capacity: Optional[Decimal] = None,
        min_volume_capacity: Optional[Decimal] = None,
        near_location: Optional[GPSLocation] = None,
        radius_km: Optional[Decimal] = None
    ) -> List[VehicleEntity]:
        """Obtener vehículos disponibles con criterios específicos."""
        try:
            queryset = Vehicle.objects.select_related('current_driver', 'owner').filter(
                status='available',
                is_active=True
            )
            
            if vehicle_type:
                queryset = queryset.filter(vehicle_type=vehicle_type.value)
            
            if min_weight_capacity:
                queryset = queryset.filter(max_weight_kg__gte=min_weight_capacity)
            
            if min_volume_capacity:
                queryset = queryset.filter(max_volume_m3__gte=min_volume_capacity)
            
            # TODO: Implementar filtro por ubicación usando PostGIS o similar
            
            vehicles_models = await sync_to_async(list)(queryset)
            
            entities = []
            for vehicle_model in vehicles_models:
                entity = await self._model_to_entity(vehicle_model)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error obteniendo vehículos disponibles: {e}")
            raise

    async def get_vehicles_by_status(self, status: VehicleStatus) -> List[VehicleEntity]:
        """Obtener vehículos por estado."""
        try:
            vehicles_models = await sync_to_async(list)(
                Vehicle.objects.select_related('current_driver', 'owner')
                .filter(status=status.value, is_active=True)
            )
            
            entities = []
            for vehicle_model in vehicles_models:
                entity = await self._model_to_entity(vehicle_model)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error obteniendo vehículos por estado {status}: {e}")
            raise

    async def get_vehicles_needing_maintenance(self) -> List[VehicleEntity]:
        """Obtener vehículos que necesitan mantenimiento."""
        try:
            # Obtener vehículos que necesitan mantenimiento según la lógica de negocio
            vehicles_models = await sync_to_async(list)(
                Vehicle.objects.select_related('current_driver', 'owner')
                .filter(is_active=True)
            )
            
            entities = []
            for vehicle_model in vehicles_models:
                entity = await self._model_to_entity(vehicle_model)
                if entity.is_maintenance_due():
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error obteniendo vehículos que necesitan mantenimiento: {e}")
            raise

    async def update(self, vehicle: VehicleEntity) -> VehicleEntity:
        """Actualizar vehículo."""
        try:
            vehicle_model = await sync_to_async(Vehicle.objects.get)(id=vehicle.id)
            
            # Actualizar campos
            vehicle_model.license_plate = vehicle.license_plate
            vehicle_model.brand = vehicle.brand
            vehicle_model.model = vehicle.model
            vehicle_model.year = vehicle.year
            vehicle_model.color = vehicle.color
            vehicle_model.vehicle_type = vehicle.vehicle_type.value
            vehicle_model.vin_number = vehicle.vin_number
            vehicle_model.status = vehicle.status.value
            vehicle_model.current_driver_id = vehicle.current_driver_id
            vehicle_model.max_weight_kg = vehicle.specifications.max_weight_kg
            vehicle_model.max_volume_m3 = vehicle.specifications.max_volume_m3
            vehicle_model.fuel_type = vehicle.specifications.fuel_type.value
            vehicle_model.fuel_capacity_liters = vehicle.specifications.fuel_capacity_liters
            vehicle_model.engine_power_hp = vehicle.specifications.engine_power_hp
            vehicle_model.transmission_type = vehicle.specifications.transmission_type
            vehicle_model.emissions_standard = vehicle.specifications.emissions_standard
            vehicle_model.registration_expiry = vehicle.registration_expiry
            vehicle_model.insurance_expiry = vehicle.insurance_expiry
            vehicle_model.total_mileage_km = vehicle.total_mileage_km
            vehicle_model.last_maintenance_date = vehicle.last_maintenance_date
            vehicle_model.updated_at = vehicle.updated_at
            
            await sync_to_async(vehicle_model.save)()
            
            # Actualizar ubicación si existe
            if vehicle.current_location:
                await self._create_vehicle_location(vehicle.id, vehicle.current_location)
            
            logger.info(f"Vehículo actualizado: {vehicle.id}")
            return vehicle
            
        except ObjectDoesNotExist:
            raise VehicleNotFound(str(vehicle.id))
        except Exception as e:
            logger.error(f"Error actualizando vehículo {vehicle.id}: {e}")
            raise

    async def delete(self, vehicle_id: UUID) -> bool:
        """Eliminar vehículo."""
        try:
            vehicle_model = await sync_to_async(Vehicle.objects.get)(id=vehicle_id)
            await sync_to_async(vehicle_model.soft_delete)()
            
            logger.info(f"Vehículo eliminado: {vehicle_id}")
            return True
            
        except ObjectDoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error eliminando vehículo {vehicle_id}: {e}")
            raise

    async def count(self, filters: Optional[dict] = None) -> int:
        """Contar vehículos con filtros opcionales."""
        try:
            queryset = Vehicle.objects.filter(is_active=True)
            
            if filters:
                queryset = self._apply_filters(queryset, filters)
            
            return await sync_to_async(queryset.count)()
            
        except Exception as e:
            logger.error(f"Error contando vehículos: {e}")
            raise

    async def _model_to_entity(self, vehicle_model: Vehicle) -> VehicleEntity:
        """Convertir modelo Django a entidad de dominio."""
        # Obtener especificaciones
        specifications = VehicleSpecifications(
            max_weight_kg=vehicle_model.max_weight_kg,
            max_volume_m3=vehicle_model.max_volume_m3,
            fuel_type=FuelType(vehicle_model.fuel_type),
            fuel_capacity_liters=vehicle_model.fuel_capacity_liters,
            engine_power_hp=vehicle_model.engine_power_hp,
            transmission_type=vehicle_model.transmission_type,
            emissions_standard=vehicle_model.emissions_standard
        )
        
        # Obtener ubicación actual
        current_location = None
        try:
            latest_location = await sync_to_async(
                VehicleLocation.objects.filter(vehicle=vehicle_model).latest
            )('created_at')
            
            current_location = GPSLocation(
                latitude=latest_location.latitude,
                longitude=latest_location.longitude,
                accuracy_meters=latest_location.accuracy_meters,
                altitude_meters=latest_location.altitude_meters,
                timestamp=latest_location.created_at
            )
        except ObjectDoesNotExist:
            pass
        
        # Obtener registros de mantenimiento
        maintenance_records = []
        maintenance_models = await sync_to_async(list)(
            MaintenanceRecordModel.objects.filter(vehicle=vehicle_model)
        )
        
        for maintenance_model in maintenance_models:
            maintenance_record = MaintenanceRecord(
                id=maintenance_model.id,
                vehicle_id=maintenance_model.vehicle_id,
                maintenance_type=maintenance_model.maintenance_type,
                description=maintenance_model.description,
                cost=maintenance_model.cost,
                performed_at=maintenance_model.performed_at,
                next_maintenance_date=maintenance_model.next_maintenance_date,
                mileage_km=maintenance_model.mileage_km,
                performed_by=maintenance_model.performed_by,
                notes=maintenance_model.notes
            )
            maintenance_records.append(maintenance_record)
        
        # Crear entidad
        return VehicleEntity(
            id=vehicle_model.id,
            license_plate=vehicle_model.license_plate,
            brand=vehicle_model.brand,
            model=vehicle_model.model,
            year=vehicle_model.year,
            color=vehicle_model.color,
            vehicle_type=VehicleType(vehicle_model.vehicle_type),
            specifications=specifications,
            status=VehicleStatus(vehicle_model.status),
            current_location=current_location,
            current_driver_id=vehicle_model.current_driver_id,
            owner_id=vehicle_model.owner_id,
            vin_number=vehicle_model.vin_number,
            registration_expiry=vehicle_model.registration_expiry,
            insurance_expiry=vehicle_model.insurance_expiry,
            last_maintenance_date=vehicle_model.last_maintenance_date,
            total_mileage_km=vehicle_model.total_mileage_km,
            created_at=vehicle_model.created_at,
            updated_at=vehicle_model.updated_at,
            maintenance_records=maintenance_records
        )

    async def _create_vehicle_location(self, vehicle_id: UUID, location: GPSLocation) -> None:
        """Crear registro de ubicación de vehículo."""
        try:
            vehicle_model = await sync_to_async(Vehicle.objects.get)(id=vehicle_id)
            
            location_model = VehicleLocation(
                vehicle=vehicle_model,
                latitude=location.latitude,
                longitude=location.longitude,
                accuracy_meters=location.accuracy_meters,
                altitude_meters=location.altitude_meters
            )
            
            await sync_to_async(location_model.save)()
            
        except Exception as e:
            logger.error(f"Error creando ubicación para vehículo {vehicle_id}: {e}")
            raise

    async def _create_maintenance_record(self, maintenance: MaintenanceRecord) -> None:
        """Crear registro de mantenimiento."""
        try:
            vehicle_model = await sync_to_async(Vehicle.objects.get)(id=maintenance.vehicle_id)
            
            maintenance_model = MaintenanceRecordModel(
                id=maintenance.id,
                vehicle=vehicle_model,
                maintenance_type=maintenance.maintenance_type,
                description=maintenance.description,
                cost=maintenance.cost,
                performed_at=maintenance.performed_at,
                next_maintenance_date=maintenance.next_maintenance_date,
                mileage_km=maintenance.mileage_km,
                performed_by=maintenance.performed_by,
                notes=maintenance.notes
            )
            
            await sync_to_async(maintenance_model.save)()
            
        except Exception as e:
            logger.error(f"Error creando registro de mantenimiento: {e}")
            raise

    def _apply_filters(self, queryset, filters: Dict[str, Any]):
        """Aplicar filtros al queryset."""
        if 'vehicle_type' in filters:
            queryset = queryset.filter(vehicle_type=filters['vehicle_type'])
        
        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])
        
        if 'owner_id' in filters:
            queryset = queryset.filter(owner_id=filters['owner_id'])
        
        if 'brand' in filters:
            queryset = queryset.filter(brand__icontains=filters['brand'])
        
        if 'model' in filters:
            queryset = queryset.filter(model__icontains=filters['model'])
        
        if 'year_from' in filters:
            queryset = queryset.filter(year__gte=filters['year_from'])
        
        if 'year_to' in filters:
            queryset = queryset.filter(year__lte=filters['year_to'])
        
        if 'available_only' in filters and filters['available_only']:
            queryset = queryset.filter(status='available')
        
        if 'maintenance_due' in filters:
            # Esto requeriría lógica más compleja en SQL
            pass
        
        return queryset
