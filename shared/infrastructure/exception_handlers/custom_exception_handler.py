"""
Custom Exception Handlers.
Manejadores de excepciones personalizados para DRF.
"""

import uuid
from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.utils import timezone
import traceback as tb


def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado para DRF.
    Proporciona respuestas JSON consistentes y logging detallado.
    """
    # Llamar al manejador de excepciones por defecto de DRF
    response = exception_handler(exc, context)
    
    # Si DRF no maneja la excepción, crear una respuesta personalizada
    if response is None:
        custom_response_data = {
            'error': 'internal_server_error',
            'message': str(exc),
            'type': type(exc).__name__,
            'traceback': tb.format_exc().strip().split('\n'),
            'timestamp': timezone.now().isoformat(),
            'path': context['request'].path if context.get('request') else None,
            'method': context['request'].method if context.get('request') else None,
            'error_id': str(uuid.uuid4())
        }
        
        return Response(
            custom_response_data,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Personalizar la respuesta para errores conocidos
    if response is not None:
        custom_response_data = {
            'error': get_error_code(exc),
            'message': get_error_message(exc, response.data),
            'details': response.data,
            'timestamp': timezone.now().isoformat(),
            'path': context['request'].path if context.get('request') else None,
            'method': context['request'].method if context.get('request') else None,
            'error_id': str(uuid.uuid4())
        }
        
        response.data = custom_response_data
    
    return response


def get_error_code(exc):
    """Obtiene el código de error basado en el tipo de excepción."""
    error_codes = {
        'ValidationError': 'validation_error',
        'NotAuthenticated': 'authentication_required',
        'PermissionDenied': 'permission_denied',
        'NotFound': 'not_found',
        'MethodNotAllowed': 'method_not_allowed',
        'Throttled': 'rate_limit_exceeded',
        'ParseError': 'parse_error',
    }
    
    return error_codes.get(type(exc).__name__, 'unknown_error')


def get_error_message(exc, data):
    """Extrae el mensaje de error de manera consistente."""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Para errores de validación con múltiples campos
            messages = []
            for field, errors in exc.detail.items():
                if isinstance(errors, list):
                    field_errors = [str(error) for error in errors]
                    messages.append(f"{field}: {', '.join(field_errors)}")
                else:
                    messages.append(f"{field}: {str(errors)}")
            return '; '.join(messages)
        elif isinstance(exc.detail, list):
            return '; '.join([str(error) for error in exc.detail])
        else:
            return str(exc.detail)
    
    return str(exc)
