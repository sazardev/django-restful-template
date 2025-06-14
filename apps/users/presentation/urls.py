"""
User API URLs.
Configuración de rutas para la API de usuarios.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.presentation.views import (
    UserViewSet,
    PasswordResetView,
    PasswordResetConfirmView
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

# URLs principales
urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
    
    # Rutas adicionales de autenticación
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]

# Nombres de las rutas para referencia
app_name = 'users'
