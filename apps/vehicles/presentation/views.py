"""
Vehicle presentation layer - REST API views
Implements RESTful endpoints for vehicle management following Clean Architecture
"""

from django.db import transaction
from django.db import models
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from shared.infrastructure.pagination import StandardPagination
from shared.infrastructure.permissions import IsOwnerOrReadOnlyPermission
from apps.vehicles.application.services import VehicleApplicationService
from apps.vehicles.application.dtos import (
    CreateVehicleDTO,
    UpdateVehicleDTO,
    VehicleSearchCriteriaDTO
)
from apps.vehicles.infrastructure.models import Vehicle, VehicleLocation, MaintenanceRecord
from apps.vehicles.presentation.serializers import (
    VehicleSerializer,
    CreateVehicleSerializer,
    UpdateVehicleSerializer,
    VehicleListSerializer
)


class VehicleViewSet(ModelViewSet):
    """
    ViewSet for Vehicle CRUD operations
    
    Provides:
    - GET /vehicles/ - List vehicles with filtering and pagination
    - POST /vehicles/ - Create new vehicle
    - GET /vehicles/{id}/ - Retrieve vehicle details
    - PUT /vehicles/{id}/ - Update vehicle
    - PATCH /vehicles/{id}/ - Partial update vehicle
    - DELETE /vehicles/{id}/ - Delete vehicle
    - GET /vehicles/{id}/history/ - Get vehicle history
    - POST /vehicles/{id}/set_maintenance/ - Set maintenance status
    """
    
    queryset = Vehicle.objects.select_related('owner', 'category').prefetch_related('maintenances')
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnlyPermission]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtering options
    filterset_fields = {
        'vehicle_type': ['exact', 'in'],
        'status': ['exact', 'in'],
        'category': ['exact'],
        'owner': ['exact'],
        'year': ['exact', 'gte', 'lte'],
        'price': ['exact', 'gte', 'lte'],
        'mileage': ['exact', 'gte', 'lte'],
        'created_at': ['date', 'date__gte', 'date__lte'],
    }
    
    # Search fields
    search_fields = ['license_plate', 'brand', 'model', 'description']
    
    # Ordering options
    ordering_fields = ['created_at', 'updated_at', 'price', 'year', 'mileage']
    ordering = ['-created_at']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = VehicleApplicationService()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CreateVehicleSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateVehicleSerializer
        elif self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters
        """
        queryset = super().get_queryset()
        
        # Filter by user role
        if not self.request.user.is_staff:
            # Regular users only see their own vehicles or public ones
            queryset = queryset.filter(
                models.Q(owner=self.request.user) |
                models.Q(is_public=True)
            )
        
        return queryset
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def list(self, request, *args, **kwargs):
        """
        List vehicles with advanced filtering and caching
        
        Query Parameters:
        - vehicle_type: Filter by vehicle type
        - status: Filter by status
        - category: Filter by category ID
        - min_price, max_price: Price range filter
        - min_year, max_year: Year range filter
        - search: Search in license_plate, brand, model, description
        - ordering: Sort by fields (prefix with - for descending)
        """
        return super().list(request, *args, **kwargs)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new vehicle
        
        Automatically sets the owner to the current user
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create DTO from validated data
        create_dto = CreateVehicleDTO(
            owner_id=request.user.id,
            **serializer.validated_data
        )
        
        # Use application service to create vehicle
        vehicle = self.service.create_vehicle(create_dto)
        
        # Return serialized response
        response_serializer = VehicleSerializer(vehicle)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED
        )
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update vehicle using application service"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Create DTO from validated data
        update_dto = UpdateVehicleDTO(**serializer.validated_data)
        
        # Use application service to update vehicle
        vehicle = self.service.update_vehicle(instance.id, update_dto)
        
        # Return serialized response
        response_serializer = VehicleSerializer(vehicle)
        return Response(response_serializer.data)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Soft delete vehicle"""
        instance = self.get_object()
        self.service.delete_vehicle(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get vehicle history including maintenances, auctions, etc.
        
        GET /vehicles/{id}/history/
        """
        vehicle = self.get_object()
        history_data = self.service.get_vehicle_history(vehicle.id)
        
        return Response({
            'vehicle_id': vehicle.id,
            'license_plate': vehicle.license_plate,
            'history': history_data
        })
    
    @action(detail=True, methods=['post'])
    def set_maintenance(self, request, pk=None):
        """
        Set vehicle maintenance status
        
        POST /vehicles/{id}/set_maintenance/
        Body: {
            "maintenance_type": "preventive|corrective|emergency",
            "description": "Maintenance description",
            "scheduled_date": "2024-01-15T10:00:00Z"
        }
        """
        vehicle = self.get_object()
        
        maintenance_type = request.data.get('maintenance_type')
        description = request.data.get('description', '')
        scheduled_date = request.data.get('scheduled_date')
        
        if not maintenance_type:
            return Response(
                {'error': 'maintenance_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = self.service.schedule_maintenance(
                vehicle.id,
                maintenance_type,
                description,
                scheduled_date
            )
            
            return Response({
                'message': 'Maintenance scheduled successfully',
                'maintenance_id': result.get('maintenance_id'),
                'vehicle_status': result.get('vehicle_status')
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get vehicle statistics for the current user
        
        GET /vehicles/statistics/
        """
        stats = self.service.get_user_vehicle_statistics(request.user.id)
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def search_advanced(self, request):
        """
        Advanced search with custom criteria
        
        GET /vehicles/search_advanced/?criteria={}
        """
        criteria_data = request.query_params.get('criteria', '{}')
        
        try:
            import json
            criteria_dict = json.loads(criteria_data)
            
            # Create search criteria DTO
            search_criteria = VehicleSearchCriteriaDTO(**criteria_dict)
            
            # Perform search using application service
            vehicles = self.service.search_vehicles(search_criteria)
            
            # Serialize results
            serializer = VehicleListSerializer(vehicles, many=True)
            
            return Response({
                'count': len(vehicles),
                'results': serializer.data
            })
            
        except (json.JSONDecodeError, TypeError) as e:
            return Response(
                {'error': 'Invalid criteria format'},
                status=status.HTTP_400_BAD_REQUEST
            )


class VehicleLocationViewSet(ModelViewSet):
    """
    ViewSet para gestión de ubicaciones de vehículos.
    
    Provides:
    - GET /vehicles/{vehicle_id}/locations/ - Lista ubicaciones del vehículo
    - POST /vehicles/{vehicle_id}/locations/ - Agregar nueva ubicación
    - GET /vehicles/{vehicle_id}/locations/{id}/ - Detalle de ubicación
    - PUT /vehicles/{vehicle_id}/locations/{id}/ - Actualizar ubicación
    - DELETE /vehicles/{vehicle_id}/locations/{id}/ - Eliminar ubicación
    """
    
    from apps.vehicles.infrastructure.models import VehicleLocation
    from apps.vehicles.presentation.serializers import VehicleLocationSerializer
    
    queryset = VehicleLocation.objects.select_related('vehicle')
    serializer_class = VehicleLocationSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnlyPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['vehicle', 'vehicle__status', 'vehicle__vehicle_type']
    search_fields = ['vehicle__license_plate', 'vehicle__brand', 'vehicle__model']
    ordering_fields = ['created_at', 'latitude', 'longitude']
    ordering = ['-created_at']
    pagination_class = StandardPagination

    def get_queryset(self):
        """Filtrar ubicaciones basadas en permisos del usuario."""
        queryset = super().get_queryset()
        
        # Filter by vehicle_id if provided in URL
        vehicle_id = self.kwargs.get('vehicle_pk')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        # Los administradores pueden ver todas las ubicaciones
        if self.request.user.is_staff:
            return queryset
        
        # Los propietarios solo pueden ver ubicaciones de sus vehículos
        return queryset.filter(vehicle__owner=self.request.user)

    def perform_create(self, serializer):
        """Crear nueva ubicación de vehículo."""
        vehicle_id = self.kwargs.get('vehicle_pk')
        if vehicle_id:
            # Verificar que el usuario tiene permisos sobre el vehículo
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                if vehicle.owner != self.request.user and not self.request.user.is_staff:
                    raise PermissionDenied("No tienes permisos para agregar ubicaciones a este vehículo")
                
                serializer.save(vehicle=vehicle)
            except Vehicle.DoesNotExist:
                raise NotFound("Vehículo no encontrado")
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def recent(self, request, vehicle_pk=None):
        """Obtener ubicaciones recientes del vehículo."""
        if not vehicle_pk:
            return Response(
                {'error': 'Se requiere vehicle_pk'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(vehicle_id=vehicle_pk)[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tracking(self, request, vehicle_pk=None):
        """Obtener tracking en tiempo real del vehículo."""
        if not vehicle_pk:
            return Response(
                {'error': 'Se requiere vehicle_pk'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener parámetros de tiempo
        from datetime import datetime, timedelta
        hours = int(request.query_params.get('hours', 24))
        since = datetime.now() - timedelta(hours=hours)
        
        queryset = self.get_queryset().filter(
            vehicle_id=vehicle_pk,
            created_at__gte=since
        ).order_by('created_at')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'vehicle_id': vehicle_pk,
            'period_hours': hours,
            'locations': serializer.data
        })


class VehicleMaintenanceViewSet(ModelViewSet):
    """
    ViewSet para gestión de mantenimiento de vehículos.
    
    Provides:
    - GET /vehicles/{vehicle_id}/maintenance/ - Lista mantenimientos del vehículo
    - POST /vehicles/{vehicle_id}/maintenance/ - Crear nuevo mantenimiento
    - GET /vehicles/{vehicle_id}/maintenance/{id}/ - Detalle de mantenimiento
    - PUT /vehicles/{vehicle_id}/maintenance/{id}/ - Actualizar mantenimiento
    - DELETE /vehicles/{vehicle_id}/maintenance/{id}/ - Eliminar mantenimiento
    """
    
    from apps.vehicles.infrastructure.models import MaintenanceRecord
    from apps.vehicles.presentation.serializers import MaintenanceRecordSerializer
    
    queryset = MaintenanceRecord.objects.select_related('vehicle')
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnlyPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['vehicle', 'maintenance_type', 'vehicle__status']
    search_fields = ['description', 'performed_by', 'vehicle__license_plate']
    ordering_fields = ['performed_at', 'cost', 'created_at']
    ordering = ['-performed_at']
    pagination_class = StandardPagination

    def get_queryset(self):
        """Filtrar mantenimientos basados en permisos del usuario."""
        queryset = super().get_queryset()
        
        # Filter by vehicle_id if provided in URL
        vehicle_id = self.kwargs.get('vehicle_pk')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        # Los administradores pueden ver todos los mantenimientos
        if self.request.user.is_staff:
            return queryset
        
        # Los propietarios solo pueden ver mantenimientos de sus vehículos
        return queryset.filter(vehicle__owner=self.request.user)

    def perform_create(self, serializer):
        """Crear nuevo registro de mantenimiento."""
        vehicle_id = self.kwargs.get('vehicle_pk')
        if vehicle_id:
            # Verificar permisos sobre el vehículo
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                if vehicle.owner != self.request.user and not self.request.user.is_staff:
                    raise PermissionDenied("No tienes permisos para agregar mantenimiento a este vehículo")
                
                serializer.save(vehicle=vehicle)
            except Vehicle.DoesNotExist:
                raise NotFound("Vehículo no encontrado")
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def summary(self, request, vehicle_pk=None):
        """Obtener resumen de mantenimiento del vehículo."""
        if not vehicle_pk:
            return Response(
                {'error': 'Se requiere vehicle_pk'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.db.models import Sum, Count, Avg
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset().filter(vehicle_id=vehicle_pk)
        
        # Métricas generales
        summary = queryset.aggregate(
            total_records=Count('id'),
            total_cost=Sum('cost'),
            average_cost=Avg('cost')
        )
        
        # Mantenimientos por tipo
        maintenance_by_type = queryset.values('maintenance_type').annotate(
            count=Count('id'),
            total_cost=Sum('cost')
        )
        
        # Mantenimientos recientes (últimos 6 meses)
        six_months_ago = datetime.now() - timedelta(days=180)
        recent_maintenance = queryset.filter(
            performed_at__gte=six_months_ago
        ).order_by('-performed_at')[:5]
        
        return Response({
            'vehicle_id': vehicle_pk,
            'summary': summary,
            'by_type': list(maintenance_by_type),
            'recent': self.get_serializer(recent_maintenance, many=True).data
        })

    @action(detail=False, methods=['post'])
    def schedule(self, request, vehicle_pk=None):
        """Programar mantenimiento futuro."""
        if not vehicle_pk:
            return Response(
                {'error': 'Se requiere vehicle_pk'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.vehicles.presentation.serializers import VehicleMaintenanceSerializer
        
        serializer = VehicleMaintenanceSerializer(data=request.data)
        if serializer.is_valid():
            # Verificar permisos sobre el vehículo
            try:
                vehicle = Vehicle.objects.get(id=vehicle_pk)
                if vehicle.owner != self.request.user and not self.request.user.is_staff:
                    raise PermissionDenied("No tienes permisos para programar mantenimiento en este vehículo")
                
                # Crear registro de mantenimiento programado
                maintenance = MaintenanceRecord.objects.create(
                    vehicle=vehicle,
                    maintenance_type=serializer.validated_data['maintenance_type'],
                    description=serializer.validated_data['description'],
                    cost=serializer.validated_data['cost'],
                    scheduled_date=serializer.validated_data.get('scheduled_date'),
                    notes=serializer.validated_data.get('notes', '')
                )
                
                return Response(
                    self.get_serializer(maintenance).data,
                    status=status.HTTP_201_CREATED
                )
            except Vehicle.DoesNotExist:
                return Response(
                    {'error': 'Vehículo no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleAnalyticsView(APIView):
    """
    Vista para análisis y métricas de vehículos.
    
    Provides:
    - GET /vehicles/analytics/fleet/ - Análisis de flota
    - GET /vehicles/analytics/utilization/ - Análisis de utilización
    - GET /vehicles/analytics/costs/ - Análisis de costos
    - GET /vehicles/analytics/performance/ - Análisis de rendimiento
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """Obtener análisis general de vehículos."""
        analytics_type = request.query_params.get('type', 'fleet')
        
        if analytics_type == 'fleet':
            return self.fleet_analytics(request)
        elif analytics_type == 'utilization':
            return self.utilization_analytics(request)
        elif analytics_type == 'costs':
            return self.costs_analytics(request)
        elif analytics_type == 'performance':
            return self.performance_analytics(request)
        else:
            return Response(
                {'error': 'Tipo de análisis no válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def fleet_analytics(self, request):
        """Análisis de flota."""
        from django.db.models import Count, Q
        
        # Filtrar vehículos según permisos del usuario
        queryset = Vehicle.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(owner=request.user)
        
        # Métricas de flota
        fleet_metrics = queryset.aggregate(
            total_vehicles=Count('id'),
            active_vehicles=Count('id', filter=Q(status='active')),
            in_maintenance=Count('id', filter=Q(status='maintenance')),
            available_vehicles=Count('id', filter=Q(status='available'))
        )
        
        # Distribución por tipo
        by_type = queryset.values('vehicle_type').annotate(
            count=Count('id')
        )
        
        # Distribución por año
        by_year = queryset.values('year').annotate(
            count=Count('id')
        ).order_by('year')
        
        return Response({
            'fleet_metrics': fleet_metrics,
            'distribution_by_type': list(by_type),
            'distribution_by_year': list(by_year)
        })
    
    def utilization_analytics(self, request):
        """Análisis de utilización."""
        # Esta es una implementación básica
        # En un sistema real, se calcularía basado en datos de ubicación y uso
        
        queryset = Vehicle.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(owner=request.user)
        
        # Simulación de métricas de utilización
        utilization_data = []
        for vehicle in queryset:
            utilization_data.append({
                'vehicle_id': str(vehicle.id),
                'license_plate': vehicle.license_plate,
                'utilization_rate': 75.5,  # Esto se calcularía basado en datos reales
                'active_hours': 180.0,
                'idle_hours': 20.0,
                'total_distance_km': 2500.0
            })
        
        return Response({
            'utilization_metrics': utilization_data
        })
    
    def costs_analytics(self, request):
        """Análisis de costos."""
        from django.db.models import Sum
        from datetime import datetime, timedelta
        
        queryset = Vehicle.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(owner=request.user)
        
        # Costos de mantenimiento por vehículo
        maintenance_costs = []
        for vehicle in queryset:
            total_cost = vehicle.maintenance_records.aggregate(
                total=Sum('cost')
            )['total'] or 0
            
            maintenance_costs.append({
                'vehicle_id': str(vehicle.id),
                'license_plate': vehicle.license_plate,
                'total_maintenance_cost': float(total_cost),
                'maintenance_records_count': vehicle.maintenance_records.count()
            })
        
        return Response({
            'maintenance_costs': maintenance_costs
        })
    
    def performance_analytics(self, request):
        """Análisis de rendimiento."""
        # Implementación básica para rendimiento de vehículos
        
        queryset = Vehicle.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(owner=request.user)
        
        performance_data = []
        for vehicle in queryset:
            # Simulación de métricas de rendimiento
            performance_data.append({
                'vehicle_id': str(vehicle.id),
                'license_plate': vehicle.license_plate,
                'efficiency_score': 85.2,  # Se calcularía basado en datos reales
                'fuel_efficiency': 12.5,
                'maintenance_frequency': 2.1,
                'uptime_percentage': 94.3
            })
        
        return Response({
            'performance_metrics': performance_data
        })
