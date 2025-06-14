"""
Exception Middleware.
Middleware para manejo global de excepciones.
"""

import traceback
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class ExceptionMiddleware(MiddlewareMixin):
    """
    Middleware para capturar y manejar excepciones no controladas.
    Proporciona respuestas JSON consistentes para errores 500.
    """
    
    def process_exception(self, request, exception):
        """Procesar excepciones no manejadas."""
        
        # Log del error completo
        logger.error(
            f"Unhandled exception in {request.method} {request.path}",
            exc_info=True,
            extra={
                'request_data': self.get_request_data(request),
                'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
        
        # En desarrollo, mostrar traceback completo
        if settings.DEBUG:
            error_details = {
                'error': 'internal_server_error',
                'message': str(exception),
                'type': exception.__class__.__name__,
                'traceback': traceback.format_exc().split('\n'),
            }
        else:
            # En producción, mostrar mensaje genérico
            error_details = {
                'error': 'internal_server_error',
                'message': 'Ha ocurrido un error interno en el servidor',
            }
        
        # Agregar información adicional
        error_details.update({
            'timestamp': self.get_current_timestamp(),
            'path': request.path,
            'method': request.method,
        })
        
        # Generar ID único para tracking
        import uuid
        error_details['error_id'] = str(uuid.uuid4())
        
        # Notificar a sistemas de monitoreo
        self.notify_monitoring_systems(exception, request, error_details['error_id'])
        
        # Retornar respuesta JSON
        return JsonResponse(
            error_details,
            status=500,
            json_dumps_params={'indent': 2} if settings.DEBUG else {}
        )
    
    def get_request_data(self, request):
        """Obtener datos del request de forma segura."""
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.content_type == 'application/json':
                    return json.loads(request.body)
                else:
                    return dict(request.POST)
        except:
            return None
    
    def get_client_ip(self, request):
        """Obtener IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def get_current_timestamp(self):
        """Obtener timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def notify_monitoring_systems(self, exception, request, error_id):
        """Notificar a sistemas de monitoreo externos."""
        try:
            # Enviar a Sentry si está configurado
            if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
                self.send_to_sentry(exception, request, error_id)
            
            # Enviar notificación por email a administradores
            if not settings.DEBUG:
                self.send_admin_notification(exception, request, error_id)
            
        except Exception as e:
            logger.error(f"Error notifying monitoring systems: {e}")
    
    def send_to_sentry(self, exception, request, error_id):
        """Enviar error a Sentry."""
        try:
            import sentry_sdk
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("error_id", error_id)
                scope.set_context("request", {
                    "method": request.method,
                    "path": request.path,
                    "user": str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    "ip": self.get_client_ip(request),
                })
                sentry_sdk.capture_exception(exception)
        except ImportError:
            logger.warning("Sentry not configured")
        except Exception as e:
            logger.error(f"Error sending to Sentry: {e}")
    
    def send_admin_notification(self, exception, request, error_id):
        """Enviar notificación por email a administradores."""
        try:
            from django.core.mail import mail_admins
            
            subject = f"Error 500 en Logistics API - {error_id}"
            message = f"""
            Se ha producido un error 500 en la aplicación.
            
            Error ID: {error_id}
            Excepción: {exception.__class__.__name__}: {str(exception)}
            Ruta: {request.method} {request.path}
            Usuario: {request.user if hasattr(request, 'user') else 'Anonymous'}
            IP: {self.get_client_ip(request)}
            Timestamp: {self.get_current_timestamp()}
            
            Por favor, revise los logs para más detalles.
            """
            
            mail_admins(subject, message, fail_silently=True)
            
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de todas las requests.
    Útil para debugging y monitoreo.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Log de request entrante."""
        if settings.DEBUG:
            logger.debug(
                f"Incoming request: {request.method} {request.path}",
                extra={
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    'ip': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
    
    def process_response(self, request, response):
        """Log de response saliente."""
        if settings.DEBUG:
            logger.debug(
                f"Outgoing response: {request.method} {request.path} -> {response.status_code}",
                extra={
                    'status_code': response.status_code,
                    'content_type': response.get('Content-Type', ''),
                }
            )
        return response
    
    def get_client_ip(self, request):
        """Obtener IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
