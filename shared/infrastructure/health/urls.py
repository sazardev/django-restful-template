"""
Health check URLs for system monitoring.
"""

from django.urls import path
from .views import (
    HealthCheckView,
    DetailedHealthCheckView,
    ReadinessView,
    LivenessView,
    simple_health_check
)

app_name = 'health'

urlpatterns = [
    # Health check básico
    path('', HealthCheckView.as_view(), name='health-check'),
    path('simple/', simple_health_check, name='simple-health-check'),
    
    # Health check detallado
    path('detailed/', DetailedHealthCheckView.as_view(), name='detailed-health-check'),
    
    # Kubernetes health checks
    path('ready/', ReadinessView.as_view(), name='readiness-check'),
    path('live/', LivenessView.as_view(), name='liveness-check'),
    
    # Alias para compatibilidad
    path('status/', HealthCheckView.as_view(), name='status'),
    path('ping/', HealthCheckView.as_view(), name='ping'),
]
