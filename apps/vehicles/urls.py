"""
Vehicle URLs Configuration.
Configuración de URLs para el sistema de vehículos.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .presentation.views import (
    VehicleViewSet,
    VehicleLocationViewSet,
    VehicleMaintenanceViewSet,
    VehicleAnalyticsView
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'locations', VehicleLocationViewSet, basename='vehicle-location')
router.register(r'maintenance', VehicleMaintenanceViewSet, basename='vehicle-maintenance')

app_name = 'vehicles'

urlpatterns = [
    # API RESTful endpoints
    path('api/v1/', include(router.urls)),
    
    # Endpoints específicos de análisis
    path('api/v1/analytics/', VehicleAnalyticsView.as_view(), name='analytics'),
    path('api/v1/analytics/fleet/', VehicleAnalyticsView.as_view(), {'metrics_type': 'fleet'}, name='fleet-analytics'),
    path('api/v1/analytics/utilization/', VehicleAnalyticsView.as_view(), {'metrics_type': 'utilization'}, name='utilization-analytics'),
    path('api/v1/analytics/maintenance/', VehicleAnalyticsView.as_view(), {'metrics_type': 'maintenance'}, name='maintenance-analytics'),
    
    # Endpoints específicos de vehículos
    path('api/v1/vehicles/<uuid:vehicle_id>/assign-driver/', VehicleViewSet.as_view({'post': 'assign_driver'}), name='assign-driver'),
    path('api/v1/vehicles/<uuid:vehicle_id>/unassign-driver/', VehicleViewSet.as_view({'post': 'unassign_driver'}), name='unassign-driver'),
    path('api/v1/vehicles/<uuid:vehicle_id>/update-location/', VehicleViewSet.as_view({'post': 'update_location'}), name='update-location'),
    path('api/v1/vehicles/<uuid:vehicle_id>/start-maintenance/', VehicleViewSet.as_view({'post': 'start_maintenance'}), name='start-maintenance'),
    path('api/v1/vehicles/<uuid:vehicle_id>/complete-maintenance/', VehicleViewSet.as_view({'post': 'complete_maintenance'}), name='complete-maintenance'),
    
    # Endpoints de búsqueda y filtros
    path('api/v1/vehicles/search/', VehicleViewSet.as_view({'get': 'search'}), name='search-vehicles'),
    path('api/v1/vehicles/available/', VehicleViewSet.as_view({'get': 'available'}), name='available-vehicles'),
    path('api/v1/vehicles/maintenance-due/', VehicleViewSet.as_view({'get': 'maintenance_due'}), name='maintenance-due'),
    path('api/v1/vehicles/near-location/', VehicleViewSet.as_view({'get': 'near_location'}), name='near-location'),
    
    # Endpoints de ubicación
    path('api/v1/vehicles/<uuid:vehicle_id>/locations/', VehicleLocationViewSet.as_view({'get': 'list', 'post': 'create'}), name='vehicle-locations'),
    path('api/v1/vehicles/<uuid:vehicle_id>/route/', VehicleLocationViewSet.as_view({'get': 'route'}), name='vehicle-route'),
    path('api/v1/vehicles/<uuid:vehicle_id>/current-location/', VehicleLocationViewSet.as_view({'get': 'current_location'}), name='current-location'),
    
    # Endpoints de mantenimiento
    path('api/v1/vehicles/<uuid:vehicle_id>/maintenance-history/', VehicleMaintenanceViewSet.as_view({'get': 'history'}), name='maintenance-history'),
    path('api/v1/vehicles/<uuid:vehicle_id>/schedule-maintenance/', VehicleMaintenanceViewSet.as_view({'post': 'schedule'}), name='schedule-maintenance'),
    path('api/v1/maintenance/<uuid:maintenance_id>/complete/', VehicleMaintenanceViewSet.as_view({'post': 'complete'}), name='complete-maintenance-record'),
]

# Patrones adicionales para WebSocket (si se implementa)
websocket_urlpatterns = [
    # path('ws/vehicles/<uuid:vehicle_id>/tracking/', VehicleTrackingConsumer.as_asgi()),
    # path('ws/vehicles/fleet-status/', FleetStatusConsumer.as_asgi()),
]
