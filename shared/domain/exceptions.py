"""
Shared Domain Exceptions.
Excepciones base del dominio.
"""


class DomainException(Exception):
    """Excepción base del dominio."""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationException(DomainException):
    """Excepción de validación."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Error de validación en {field}: {message}")


class ValidationError(ValidationException):
    """Alias for ValidationException to maintain compatibility"""
    pass


class BusinessRuleException(DomainException):
    """Excepción de regla de negocio."""
    
    def __init__(self, rule: str, message: str):
        self.rule = rule
        self.message = message
        super().__init__(f"Regla de negocio violada ({rule}): {message}")


class NotFoundException(DomainException):
    """Entidad no encontrada."""
    
    def __init__(self, entity_type: str, identifier: str):
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"{entity_type} no encontrado: {identifier}")


class ConflictException(DomainException):
    """Conflicto de estado o datos."""
    
    def __init__(self, message: str, conflicting_data: dict = None):
        self.conflicting_data = conflicting_data or {}
        super().__init__(message)


class PermissionDeniedException(DomainException):
    """Permisos insuficientes."""
    
    def __init__(self, action: str, resource: str):
        self.action = action
        self.resource = resource
        super().__init__(f"Permiso denegado para {action} en {resource}")


class ConcurrencyException(DomainException):
    """Error de concurrencia."""
    
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            f"Conflicto de concurrencia en {entity_type} {entity_id}"
        )
