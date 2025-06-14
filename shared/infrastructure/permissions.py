"""
Shared Custom Permissions.
Permisos personalizados para la API.
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsOwnerOrAdminPermission(permissions.BasePermission):
    """
    Permiso personalizado que permite acceso solo al propietario del objeto
    o a administradores.
    """
    
    def has_permission(self, request, view):
        """Verificar permisos a nivel de vista."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Verificar permisos a nivel de objeto."""
        # Superusuarios siempre tienen acceso
        if request.user.is_superuser:
            return True
        
        # Administradores pueden acceder a todo
        if hasattr(request.user, 'role') and request.user.role == 'super_admin':
            return True
        
        # El propietario puede acceder a su propio objeto
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif isinstance(obj, User):
            return obj == request.user
        
        return False


class IsLogisticsManagerPermission(permissions.BasePermission):
    """Permiso para gestores logísticos."""
    
    def has_permission(self, request, view):
        """Verificar si el usuario es gestor logístico."""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ['super_admin', 'logistics_manager']
        )


class IsFleetManagerPermission(permissions.BasePermission):
    """Permiso para gestores de flota."""
    
    def has_permission(self, request, view):
        """Verificar si el usuario es gestor de flota."""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ['super_admin', 'fleet_manager']
        )


class IsAuctionManagerPermission(permissions.BasePermission):
    """Permiso para gestores de subastas."""
    
    def has_permission(self, request, view):
        """Verificar si el usuario es gestor de subastas."""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ['super_admin', 'auction_manager']
        )


class IsDriverPermission(permissions.BasePermission):
    """Permiso para conductores."""
    
    def has_permission(self, request, view):
        """Verificar si el usuario es conductor."""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ['driver']
        )


class IsClientPermission(permissions.BasePermission):
    """Permiso para clientes."""
    
    def has_permission(self, request, view):
        """Verificar si el usuario es cliente."""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ['client']
        )


class DynamicRolePermission(permissions.BasePermission):
    """
    Permiso dinámico basado en roles.
    Permite configurar roles permitidos por vista.
    """
    
    def __init__(self, allowed_roles=None):
        self.allowed_roles = allowed_roles or []
    
    def has_permission(self, request, view):
        """Verificar permisos dinámicos."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios siempre tienen acceso
        if request.user.is_superuser:
            return True
        
        # Verificar rol específico
        if hasattr(request.user, 'role'):
            return request.user.role in self.allowed_roles
        
        return False


class ResourcePermission(permissions.BasePermission):
    """
    Permiso basado en recursos específicos.
    Utiliza el método can_access_resource del usuario.
    """
    
    def __init__(self, resource=None):
        self.resource = resource
    
    def has_permission(self, request, view):
        """Verificar acceso al recurso."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Si no se especifica recurso, permitir acceso autenticado
        if not self.resource:
            return True
        
        # Usar método del modelo de usuario
        if hasattr(request.user, 'can_access_resource'):
            return request.user.can_access_resource(self.resource)
        
        return False


class ReadOnlyOrOwnerPermission(permissions.BasePermission):
    """
    Permiso que permite lectura a todos los autenticados,
    pero escritura solo al propietario.
    """
    
    def has_permission(self, request, view):
        """Verificar permisos básicos."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Verificar permisos de objeto."""
        # Lectura permitida a todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo al propietario o admin
        if request.user.is_superuser:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif isinstance(obj, User):
            return obj == request.user
        
        return False


class TimeBasedPermission(permissions.BasePermission):
    """
    Permiso basado en horarios.
    Útil para restringir acceso a ciertas horas.
    """
    
    def __init__(self, start_hour=0, end_hour=23):
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def has_permission(self, request, view):
        """Verificar permisos basados en tiempo."""
        from datetime import datetime
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        current_hour = datetime.now().hour
        
        if self.start_hour <= self.end_hour:
            return self.start_hour <= current_hour <= self.end_hour
        else:  # Horario que cruza medianoche
            return current_hour >= self.start_hour or current_hour <= self.end_hour


class IsOwnerOrReadOnlyPermission(permissions.BasePermission):
    """
    Permission that allows read-only access to any user,
    but only allows owners to edit their objects.
    """
    
    def has_permission(self, request, view):
        """Check permissions at view level."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check permissions at object level."""
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner of the object
        return obj.owner == request.user


# Alias for compatibility  
IsOwnerOrReadOnly = IsOwnerOrReadOnlyPermission
