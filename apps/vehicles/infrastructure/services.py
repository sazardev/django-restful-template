"""
Vehicle Infrastructure Services.
Servicios de infraestructura para vehículos.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from django.core.cache import cache
from django.db.models import Avg, Count, Sum
from asgiref.sync import sync_to_async

from apps.vehicles.domain.entities import VehicleEntity, GPSLocation
from apps.vehicles.domain.interfaces import (
    VehicleLocationServiceInterface,
    VehicleMaintenanceServiceInterface,
    VehicleAnalyticsServiceInterface,
    VehicleEventServiceInterface
)
from shared.infrastructure.events import EventBus
from .models import Vehicle, VehicleLocation, MaintenanceRecord

logger = logging.getLogger(__name__)


class VehicleLocationService(VehicleLocationServiceInterface):
    """Servicio para gestión de ubicación de vehículos."""

    def __init__(self, cache_timeout: int = 300):
        self.cache_timeout = cache_timeout

    async def update_vehicle_location(
        self,
        vehicle_id: UUID,
        location: GPSLocation
    ) -> bool:
        """Actualizar ubicación de un vehículo."""
        try:
            # Obtener vehículo
            vehicle = await sync_to_async(Vehicle.objects.get)(id=vehicle_id)
            
            # Crear registro de ubicación
            location_record = VehicleLocation(
                vehicle=vehicle,
                latitude=location.latitude,
                longitude=location.longitude,
                accuracy_meters=location.accuracy_meters,
                altitude_meters=location.altitude_meters
            )
            
            await sync_to_async(location_record.save)()
            
            # Actualizar caché con la ubicación más reciente
            cache_key = f"vehicle_location_{vehicle_id}"
            cache.set(cache_key, {
                'latitude': float(location.latitude),
                'longitude': float(location.longitude),
                'timestamp': location.timestamp.isoformat() if location.timestamp else datetime.now().isoformat(),
                'accuracy_meters': float(location.accuracy_meters) if location.accuracy_meters else None
            }, self.cache_timeout)
            
            logger.info(f"Ubicación actualizada para vehículo {vehicle_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando ubicación del vehículo {vehicle_id}: {e}")
            return False

    async def get_vehicles_near_location(
        self,
        location: GPSLocation,
        radius_km: Decimal
    ) -> List[VehicleEntity]:
        """Obtener vehículos cerca de una ubicación."""
        try:
            # Esta implementación requeriría PostGIS para cálculos geoespaciales eficientes
            # Por ahora, implementaremos una versión básica
            
            all_vehicles = await sync_to_async(list)(
                Vehicle.objects.filter(is_active=True)
                .prefetch_related('locations')
            )
            
            nearby_vehicles = []
            
            for vehicle in all_vehicles:
                # Obtener última ubicación del vehículo
                latest_location = await sync_to_async(
                    vehicle.locations.order_by('-created_at').first
                )()
                
                if latest_location:
                    vehicle_location = GPSLocation(
                        latitude=latest_location.latitude,
                        longitude=latest_location.longitude,
                        timestamp=latest_location.created_at
                    )
                    
                    # Calcular distancia
                    distance = location.distance_to(vehicle_location)
                    
                    if distance <= radius_km:
                        # Convertir a entidad (simplificado)
                        nearby_vehicles.append(vehicle)
            
            return nearby_vehicles[:50]  # Limitar resultados
            
        except Exception as e:
            logger.error(f"Error buscando vehículos cerca de ubicación: {e}")
            return []

    async def track_vehicle_route(
        self,
        vehicle_id: UUID,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[GPSLocation]:
        """Obtener ruta histórica de un vehículo."""
        try:
            queryset = VehicleLocation.objects.filter(vehicle_id=vehicle_id)
            
            if start_time:
                start_datetime = datetime.fromisoformat(start_time)
                queryset = queryset.filter(created_at__gte=start_datetime)
            
            if end_time:
                end_datetime = datetime.fromisoformat(end_time)
                queryset = queryset.filter(created_at__lte=end_datetime)
            
            locations = await sync_to_async(list)(
                queryset.order_by('created_at')
            )
            
            route = []
            for loc in locations:
                gps_location = GPSLocation(
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    accuracy_meters=loc.accuracy_meters,
                    altitude_meters=loc.altitude_meters,
                    timestamp=loc.created_at
                )
                route.append(gps_location)
            
            return route
            
        except Exception as e:
            logger.error(f"Error obteniendo ruta del vehículo {vehicle_id}: {e}")
            return []


class VehicleMaintenanceService(VehicleMaintenanceServiceInterface):
    """Servicio para gestión de mantenimiento de vehículos."""

    async def schedule_maintenance(
        self,
        vehicle_id: UUID,
        maintenance_type: str,
        scheduled_date: str,
        description: Optional[str] = None
    ) -> bool:
        """Programar mantenimiento para un vehículo."""
        try:
            # Crear registro de mantenimiento programado
            # En una implementación real, esto podría integrarse con un sistema externo
            cache_key = f"scheduled_maintenance_{vehicle_id}"
            
            scheduled_maintenance = {
                'vehicle_id': str(vehicle_id),
                'maintenance_type': maintenance_type,
                'scheduled_date': scheduled_date,
                'description': description or '',
                'status': 'scheduled',
                'created_at': datetime.now().isoformat()
            }
            
            cache.set(cache_key, scheduled_maintenance, 86400)  # 24 horas
            
            logger.info(f"Mantenimiento programado para vehículo {vehicle_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error programando mantenimiento para vehículo {vehicle_id}: {e}")
            return False

    async def complete_maintenance(
        self,
        vehicle_id: UUID,
        maintenance_data: dict
    ) -> bool:
        """Completar mantenimiento de un vehículo."""
        try:
            # En una implementación real, esto actualizaría el sistema externo
            # y marcaría el mantenimiento como completado
            
            # Limpiar mantenimiento programado
            cache_key = f"scheduled_maintenance_{vehicle_id}"
            cache.delete(cache_key)
            
            # Registrar completación
            completed_key = f"completed_maintenance_{vehicle_id}_{datetime.now().timestamp()}"
            cache.set(completed_key, maintenance_data, 86400 * 30)  # 30 días
            
            logger.info(f"Mantenimiento completado para vehículo {vehicle_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completando mantenimiento para vehículo {vehicle_id}: {e}")
            return False

    async def get_maintenance_history(
        self,
        vehicle_id: UUID
    ) -> List[dict]:
        """Obtener historial de mantenimiento de un vehículo."""
        try:
            maintenance_records = await sync_to_async(list)(
                MaintenanceRecord.objects.filter(vehicle_id=vehicle_id)
                .order_by('-performed_at')
            )
            
            history = []
            for record in maintenance_records:
                history.append({
                    'id': str(record.id),
                    'maintenance_type': record.maintenance_type,
                    'description': record.description,
                    'cost': float(record.cost),
                    'performed_at': record.performed_at.isoformat(),
                    'performed_by': record.performed_by,
                    'mileage_km': float(record.mileage_km) if record.mileage_km else None,
                    'notes': record.notes
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de mantenimiento para vehículo {vehicle_id}: {e}")
            return []


class VehicleAnalyticsService(VehicleAnalyticsServiceInterface):
    """Servicio para análisis de vehículos."""

    async def get_vehicle_utilization_stats(
        self,
        vehicle_id: Optional[UUID] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """Obtener estadísticas de utilización de vehículos."""
        try:
            # Implementación básica - en producción usaría herramientas de analytics más robustas
            
            queryset = Vehicle.objects.filter(is_active=True)
            
            if vehicle_id:
                queryset = queryset.filter(id=vehicle_id)
            
            # Calcular métricas básicas
            stats = await sync_to_async(queryset.aggregate)(
                total_vehicles=Count('id'),
                avg_mileage=Avg('total_mileage_km'),
                total_capacity_weight=Sum('max_weight_kg'),
                total_capacity_volume=Sum('max_volume_m3')
            )
            
            # Estadísticas por estado
            status_stats = {}
            for status, _ in Vehicle.VEHICLE_STATUS:
                count = await sync_to_async(
                    queryset.filter(status=status).count
                )()
                status_stats[status] = count
            
            utilization_data = {
                'total_vehicles': stats['total_vehicles'] or 0,
                'average_mileage_km': float(stats['avg_mileage'] or 0),
                'total_capacity_weight_kg': float(stats['total_capacity_weight'] or 0),
                'total_capacity_volume_m3': float(stats['total_capacity_volume'] or 0),
                'status_distribution': status_stats,
                'utilization_rate': self._calculate_utilization_rate(status_stats),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            return utilization_data
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de utilización: {e}")
            return {}

    async def get_fleet_performance_metrics(
        self,
        owner_id: Optional[UUID] = None
    ) -> dict:
        """Obtener métricas de rendimiento de la flota."""
        try:
            queryset = Vehicle.objects.filter(is_active=True)
            
            if owner_id:
                queryset = queryset.filter(owner_id=owner_id)
            
            # Métricas básicas
            vehicles = await sync_to_async(list)(queryset)
            
            if not vehicles:
                return {}
            
            # Calcular métricas
            total_vehicles = len(vehicles)
            active_vehicles = len([v for v in vehicles if v.status in ['available', 'in_use']])
            
            # Costos de mantenimiento (últimos 12 meses)
            maintenance_costs = await self._get_maintenance_costs(queryset, 12)
            
            performance_metrics = {
                'total_vehicles': total_vehicles,
                'active_vehicles': active_vehicles,
                'utilization_rate': (active_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0,
                'average_age_years': self._calculate_average_age(vehicles),
                'maintenance_cost_trend': maintenance_costs,
                'efficiency_score': self._calculate_efficiency_score(vehicles),
                'generated_at': datetime.now().isoformat()
            }
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de rendimiento: {e}")
            return {}

    async def get_maintenance_cost_analysis(
        self,
        vehicle_id: Optional[UUID] = None,
        period_months: int = 12
    ) -> dict:
        """Obtener análisis de costos de mantenimiento."""
        try:
            start_date = datetime.now() - timedelta(days=period_months * 30)
            
            queryset = MaintenanceRecord.objects.filter(
                performed_at__gte=start_date
            )
            
            if vehicle_id:
                queryset = queryset.filter(vehicle_id=vehicle_id)
            
            # Análisis por tipo de mantenimiento
            maintenance_analysis = {}
            
            for maintenance_type, _ in MaintenanceRecord.MAINTENANCE_TYPES:
                records = await sync_to_async(list)(
                    queryset.filter(maintenance_type=maintenance_type)
                )
                
                if records:
                    total_cost = sum(float(r.cost) for r in records)
                    avg_cost = total_cost / len(records)
                    
                    maintenance_analysis[maintenance_type] = {
                        'total_cost': total_cost,
                        'average_cost': avg_cost,
                        'count': len(records),
                        'frequency_days': period_months * 30 / len(records) if len(records) > 0 else 0
                    }
            
            # Tendencia mensual
            monthly_costs = await self._get_monthly_maintenance_costs(queryset, period_months)
            
            cost_analysis = {
                'period_months': period_months,
                'by_maintenance_type': maintenance_analysis,
                'monthly_trend': monthly_costs,
                'total_cost': sum(mt['total_cost'] for mt in maintenance_analysis.values()),
                'analysis_date': datetime.now().isoformat()
            }
            
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Error analizando costos de mantenimiento: {e}")
            return {}

    def _calculate_utilization_rate(self, status_stats: dict) -> float:
        """Calcular tasa de utilización."""
        total = sum(status_stats.values())
        if total == 0:
            return 0.0
        
        active = status_stats.get('available', 0) + status_stats.get('in_use', 0)
        return (active / total) * 100

    def _calculate_average_age(self, vehicles: List[Vehicle]) -> float:
        """Calcular edad promedio de vehículos."""
        if not vehicles:
            return 0.0
        
        current_year = datetime.now().year
        total_age = sum(current_year - vehicle.year for vehicle in vehicles)
        return total_age / len(vehicles)

    def _calculate_efficiency_score(self, vehicles: List[Vehicle]) -> float:
        """Calcular puntuación de eficiencia de la flota."""
        if not vehicles:
            return 0.0
        
        # Algoritmo simplificado - en producción sería más complejo
        active_count = len([v for v in vehicles if v.status in ['available', 'in_use']])
        maintenance_count = len([v for v in vehicles if v.status == 'maintenance'])
        
        total = len(vehicles)
        efficiency = ((active_count * 1.0) - (maintenance_count * 0.5)) / total * 100
        
        return max(0.0, min(100.0, efficiency))

    async def _get_maintenance_costs(self, vehicle_queryset, months: int) -> Dict[str, float]:
        """Obtener costos de mantenimiento por mes."""
        start_date = datetime.now() - timedelta(days=months * 30)
        
        vehicle_ids = await sync_to_async(list)(
            vehicle_queryset.values_list('id', flat=True)
        )
        
        maintenance_records = await sync_to_async(list)(
            MaintenanceRecord.objects.filter(
                vehicle_id__in=vehicle_ids,
                performed_at__gte=start_date
            )
        )
        
        monthly_costs = {}
        for record in maintenance_records:
            month_key = record.performed_at.strftime('%Y-%m')
            if month_key not in monthly_costs:
                monthly_costs[month_key] = 0.0
            monthly_costs[month_key] += float(record.cost)
        
        return monthly_costs

    async def _get_monthly_maintenance_costs(self, queryset, months: int) -> Dict[str, float]:
        """Obtener costos mensuales de mantenimiento."""
        records = await sync_to_async(list)(queryset)
        
        monthly_costs = {}
        for record in records:
            month_key = record.performed_at.strftime('%Y-%m')
            if month_key not in monthly_costs:
                monthly_costs[month_key] = 0.0
            monthly_costs[month_key] += float(record.cost)
        
        return monthly_costs


class VehicleEventService(VehicleEventServiceInterface):
    """Servicio para eventos de vehículos."""

    def __init__(self):
        self.event_bus = EventBus()

    async def publish_vehicle_status_changed(
        self,
        vehicle_id: UUID,
        old_status: Optional[Any],
        new_status: Any
    ) -> None:
        """Publicar evento de cambio de estado de vehículo."""
        try:
            event_data = {
                'vehicle_id': str(vehicle_id),
                'old_status': old_status.value if old_status else None,
                'new_status': new_status.value,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'vehicle_status_changed'
            }
            
            await self.event_bus.publish('vehicle.status.changed', event_data)
            logger.info(f"Evento publicado: cambio de estado de vehículo {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error publicando evento de cambio de estado: {e}")

    async def publish_vehicle_location_updated(
        self,
        vehicle_id: UUID,
        location: GPSLocation
    ) -> None:
        """Publicar evento de actualización de ubicación."""
        try:
            event_data = {
                'vehicle_id': str(vehicle_id),
                'latitude': float(location.latitude),
                'longitude': float(location.longitude),
                'accuracy_meters': float(location.accuracy_meters) if location.accuracy_meters else None,
                'timestamp': location.timestamp.isoformat() if location.timestamp else datetime.now().isoformat(),
                'event_type': 'vehicle_location_updated'
            }
            
            await self.event_bus.publish('vehicle.location.updated', event_data)
            logger.debug(f"Evento publicado: actualización de ubicación de vehículo {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error publicando evento de ubicación: {e}")

    async def publish_maintenance_due(
        self,
        vehicle_id: UUID,
        maintenance_type: str
    ) -> None:
        """Publicar evento de mantenimiento debido."""
        try:
            event_data = {
                'vehicle_id': str(vehicle_id),
                'maintenance_type': maintenance_type,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'maintenance_due'
            }
            
            await self.event_bus.publish('vehicle.maintenance.due', event_data)
            logger.info(f"Evento publicado: mantenimiento debido para vehículo {vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error publicando evento de mantenimiento debido: {e}")
