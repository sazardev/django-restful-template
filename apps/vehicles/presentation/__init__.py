"""
Vehicle Presentation Layer.
Capa de presentación para el sistema de vehículos.
"""

from .serializers import (
    VehicleSerializer,
    VehicleCreateSerializer,
    VehicleUpdateSerializer,
    VehicleLocationSerializer,
    MaintenanceRecordSerializer,
    VehicleDocumentSerializer
)
from .views import (
    VehicleViewSet,
    VehicleLocationViewSet,
    VehicleMaintenanceViewSet,
    VehicleAnalyticsView
)

__all__ = [
    # Serializers
    'VehicleSerializer',
    'VehicleCreateSerializer',
    'VehicleUpdateSerializer',
    'VehicleLocationSerializer',
    'MaintenanceRecordSerializer',
    'VehicleDocumentSerializer',
    # Views
    'VehicleViewSet',
    'VehicleLocationViewSet',
    'VehicleMaintenanceViewSet',
    'VehicleAnalyticsView',
]
