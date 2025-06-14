"""
Shared Exception Handlers.
Manejadores de excepciones personalizados para la API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError
import logging

from shared.domain.exceptions import (
    DomainException,
    ValidationException,
    BusinessRuleException,
    NotFoundException,
    ConflictException,
    PermissionDeniedException,
    ConcurrencyException
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Manejador personalizado de excepciones para la API.
    Proporciona respuestas consistentes y logging de errores.
    """
    
    # Llamar al manejador por defecto primero
    response = exception_handler(exc, context)
    
    # Si DRF no manejó la excepción, manejarla aquí
    if response is None:
        response = handle_unhandled_exceptions(exc, context)
    
    # Agregar información adicional a la respuesta
    if response is not None:
        response = enhance_error_response(response, exc, context)
    
    # Log del error
    log_exception(exc, context, response)
    
    return response


def handle_unhandled_exceptions(exc, context):
    """Manejar excepciones no manejadas por DRF."""
    
    # Excepciones de dominio
    if isinstance(exc, NotFoundException):
        return Response({
            'error': 'not_found',
            'message': str(exc),
            'details': {
                'entity_type': exc.entity_type,
                'identifier': exc.identifier
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    elif isinstance(exc, ValidationException):
        return Response({
            'error': 'validation_error',
            'message': str(exc),
            'details': {
                'field': exc.field
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, BusinessRuleException):
        return Response({
            'error': 'business_rule_violation',
            'message': str(exc),
            'details': {
                'rule': exc.rule
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    elif isinstance(exc, ConflictException):
        return Response({
            'error': 'conflict',
            'message': str(exc),
            'details': exc.conflicting_data
        }, status=status.HTTP_409_CONFLICT)
    
    elif isinstance(exc, PermissionDeniedException):
        return Response({
            'error': 'permission_denied',
            'message': str(exc),
            'details': {
                'action': exc.action,
                'resource': exc.resource
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    elif isinstance(exc, ConcurrencyException):
        return Response({
            'error': 'concurrency_error',
            'message': str(exc),
            'details': {
                'entity_type': exc.entity_type,
                'entity_id': exc.entity_id
            }
        }, status=status.HTTP_409_CONFLICT)
    
    elif isinstance(exc, DomainException):
        return Response({
            'error': 'domain_error',
            'message': str(exc),
            'code': getattr(exc, 'code', None)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Excepciones de Django
    elif isinstance(exc, DjangoValidationError):
        return Response({
            'error': 'validation_error',
            'message': 'Error de validación',
            'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, Http404):
        return Response({
            'error': 'not_found',
            'message': 'Recurso no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    elif isinstance(exc, IntegrityError):
        return Response({
            'error': 'integrity_error',
            'message': 'Error de integridad de datos'
        }, status=status.HTTP_409_CONFLICT)
    
    # Otras excepciones
    else:
        return Response({
            'error': 'internal_server_error',
            'message': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def enhance_error_response(response, exc, context):
    """Mejorar la respuesta de error con información adicional."""
    
    if response.data and isinstance(response.data, dict):
        # Agregar timestamp
        from datetime import datetime
        response.data['timestamp'] = datetime.now().isoformat()
        
        # Agregar información de la request
        request = context.get('request')
        if request:
            response.data['path'] = request.path
            response.data['method'] = request.method
        
        # Agregar información de la vista
        view = context.get('view')
        if view:
            response.data['view'] = view.__class__.__name__
        
        # Agregar código de error único para tracking
        import uuid
        response.data['error_id'] = str(uuid.uuid4())
    
    return response


def log_exception(exc, context, response):
    """Log de excepciones para monitoreo."""
    
    request = context.get('request')
    view = context.get('view')
    
    # Información básica del error
    error_info = {
        'exception_type': exc.__class__.__name__,
        'exception_message': str(exc),
        'status_code': response.status_code if response else 500,
    }
    
    # Información de la request
    if request:
        error_info.update({
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
            'ip_address': get_client_ip(request),
        })
    
    # Información de la vista
    if view:
        error_info['view'] = view.__class__.__name__
    
    # Determinar nivel de log
    if response and response.status_code >= 500:
        logger.error(f"Server Error: {error_info}", exc_info=True)
    elif response and response.status_code >= 400:
        logger.warning(f"Client Error: {error_info}")
    else:
        logger.info(f"Exception handled: {error_info}")


def get_client_ip(request):
    """Obtener IP del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Excepciones personalizadas para la capa de infraestructura
class ValidationError(Exception):
    """Error de validación de infraestructura."""
    pass


class NotFoundError(Exception):
    """Recurso no encontrado en infraestructura."""
    pass


class ServiceUnavailableError(Exception):
    """Servicio no disponible."""
    pass
