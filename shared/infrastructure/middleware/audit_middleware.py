"""
Audit Middleware.
Middleware para auditoría automática de requests.
"""

import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditoría de requests.
    Registra todas las operaciones importantes en la API.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Rutas que se deben auditar
        self.audit_paths = [
            '/api/v1/users/',
            '/api/v1/vehicles/',
            '/api/v1/auctions/',
            '/api/v1/logistics/',
        ]
        
        # Métodos que se deben auditar
        self.audit_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def process_request(self, request):
        """Procesar request antes de que llegue a la vista."""
        request._audit_start_time = time.time()
        request._audit_timestamp = timezone.now()
        
        # Capturar IP del cliente
        request._audit_ip = self.get_client_ip(request)
        
        # Capturar User Agent
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return None
    
    def process_response(self, request, response):
        """Procesar response después de la vista."""
        
        # Solo auditar si es necesario
        if self.should_audit(request):
            self.create_audit_log(request, response)
        
        return response
    
    def should_audit(self, request):
        """Determinar si se debe auditar el request."""
        
        # Auditar solo ciertos paths
        path_match = any(
            request.path.startswith(audit_path) 
            for audit_path in self.audit_paths
        )
        
        # Auditar solo ciertos métodos
        method_match = request.method in self.audit_methods
        
        # Auditar solo usuarios autenticados
        user_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        
        return path_match and method_match and user_authenticated
    
    def create_audit_log(self, request, response):
        """Crear log de auditoría."""
        try:
            # Calcular duración
            duration = None
            if hasattr(request, '_audit_start_time'):
                duration = time.time() - request._audit_start_time
            
            # Preparar datos del log
            audit_data = {
                'timestamp': getattr(request, '_audit_timestamp', timezone.now()).isoformat(),
                'user_id': str(request.user.id) if request.user.is_authenticated else None,
                'user_email': request.user.email if request.user.is_authenticated else None,
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'status_code': response.status_code,
                'ip_address': getattr(request, '_audit_ip', ''),
                'user_agent': getattr(request, '_audit_user_agent', ''),
                'duration_ms': round(duration * 1000, 2) if duration else None,
            }
            
            # Agregar datos del body para ciertos métodos
            if request.method in ['POST', 'PUT', 'PATCH']:
                audit_data['request_data'] = self.get_request_data(request)
            
            # Agregar datos de respuesta si es error
            if response.status_code >= 400:
                audit_data['response_data'] = self.get_response_data(response)
            
            # Enviar a Celery para procesamiento asíncrono
            from apps.audit.infrastructure.tasks import create_audit_log
            create_audit_log.delay(audit_data)
            
        except Exception as e:
            # No fallar si hay error en auditoría
            logger.error(f"Error creating audit log: {e}")
    
    def get_request_data(self, request):
        """Obtener datos del request body de forma segura."""
        try:
            if hasattr(request, 'data'):
                # DRF request
                return self.sanitize_sensitive_data(request.data)
            elif request.content_type == 'application/json':
                # Request JSON
                data = json.loads(request.body)
                return self.sanitize_sensitive_data(data)
            else:
                # Form data
                return self.sanitize_sensitive_data(dict(request.POST))
        except:
            return None
    
    def get_response_data(self, response):
        """Obtener datos de respuesta de forma segura."""
        try:
            if hasattr(response, 'data'):
                return response.data
            elif response.content:
                return json.loads(response.content)
        except:
            return None
    
    def sanitize_sensitive_data(self, data):
        """Remover datos sensibles del log."""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = [
            'password', 'password_confirm', 'token', 'secret',
            'api_key', 'authorization', 'credit_card', 'ssn'
        ]
        
        sanitized = data.copy()
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***REDACTED***'
        
        return sanitized
    
    def get_client_ip(self, request):
        """Obtener IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
