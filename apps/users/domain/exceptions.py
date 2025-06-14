"""
User Domain Exceptions.
Excepciones específicas del dominio de usuarios.
"""


class UserDomainException(Exception):
    """Excepción base del dominio de usuarios."""
    pass


class UserNotFoundException(UserDomainException):
    """Usuario no encontrado."""
    
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Usuario no encontrado: {identifier}")


class UserAlreadyExistsException(UserDomainException):
    """Usuario ya existe."""
    
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Usuario ya existe con {field}: {value}")


class InvalidUserDataException(UserDomainException):
    """Datos de usuario inválidos."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Datos inválidos en {field}: {message}")


class UserNotActiveException(UserDomainException):
    """Usuario no está activo."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"Usuario no está activo: {user_id}")


class InvalidPasswordException(UserDomainException):
    """Contraseña inválida."""
    
    def __init__(self, message: str = "Contraseña inválida"):
        super().__init__(message)


class EmailNotVerifiedException(UserDomainException):
    """Email no verificado."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email no verificado: {email}")


class InsufficientPermissionsException(UserDomainException):
    """Permisos insuficientes."""
    
    def __init__(self, user_id: str, required_permission: str):
        self.user_id = user_id
        self.required_permission = required_permission
        super().__init__(
            f"Usuario {user_id} no tiene permiso: {required_permission}"
        )
