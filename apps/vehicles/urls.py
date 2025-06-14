"""
Vehicle URLs Configuration
RESTful API endpoints for vehicle management
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .presentation.views import VehicleViewSet

# Router for ViewSets
router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')

app_name = 'vehicles'

urlpatterns = [
    # API RESTful endpoints
    path('api/v1/', include(router.urls)),
    
    # Additional custom endpoints are handled by the ViewSet actions:
    # GET  /api/v1/vehicles/                     - List vehicles
    # POST /api/v1/vehicles/                     - Create vehicle
    # GET  /api/v1/vehicles/{id}/                - Retrieve vehicle
    # PUT  /api/v1/vehicles/{id}/                - Update vehicle
    # PATCH /api/v1/vehicles/{id}/               - Partial update vehicle
    # DELETE /api/v1/vehicles/{id}/              - Delete vehicle
    # GET  /api/v1/vehicles/{id}/history/        - Get vehicle history
    # POST /api/v1/vehicles/{id}/set_maintenance/ - Set maintenance status
    # GET  /api/v1/vehicles/statistics/          - Get user statistics
    # GET  /api/v1/vehicles/search_advanced/     - Advanced search
]

# WebSocket URL patterns (if implemented later)
websocket_urlpatterns = [
    # path('ws/vehicles/<uuid:vehicle_id>/tracking/', VehicleTrackingConsumer.as_asgi()),
    # path('ws/vehicles/fleet-status/', FleetStatusConsumer.as_asgi()),
]
