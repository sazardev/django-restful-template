"""
Vehicle Domain Exceptions.
Excepciones específicas del dominio de vehículos.
"""

from shared.domain.exceptions import DomainException


class VehicleException(DomainException):
    """Excepción base para el dominio de vehículos."""
    pass


class VehicleNotFound(VehicleException):
    """Vehículo no encontrado."""
    
    def __init__(self, vehicle_id: str = None, license_plate: str = None):
        if vehicle_id:
            message = f"Vehículo con ID {vehicle_id} no encontrado"
        elif license_plate:
            message = f"Vehículo con placa {license_plate} no encontrado"
        else:
            message = "Vehículo no encontrado"
        super().__init__(message)


class VehicleAlreadyExists(VehicleException):
    """Vehículo ya existe."""
    
    def __init__(self, license_plate: str):
        super().__init__(f"Ya existe un vehículo con la placa {license_plate}")


class VehicleNotAvailable(VehicleException):
    """Vehículo no disponible para la operación solicitada."""
    
    def __init__(self, vehicle_id: str, current_status: str):
        super().__init__(
            f"Vehículo {vehicle_id} no disponible. Estado actual: {current_status}"
        )


class VehicleInUse(VehicleException):
    """Vehículo actualmente en uso."""
    
    def __init__(self, vehicle_id: str, driver_id: str = None):
        message = f"Vehículo {vehicle_id} está actualmente en uso"
        if driver_id:
            message += f" por el conductor {driver_id}"
        super().__init__(message)


class InvalidVehicleOperation(VehicleException):
    """Operación no válida para el estado actual del vehículo."""
    pass


class VehicleMaintenanceError(VehicleException):
    """Error relacionado con el mantenimiento del vehículo."""
    pass


class InvalidLocationData(VehicleException):
    """Datos de ubicación inválidos."""
    
    def __init__(self, details: str = None):
        message = "Datos de ubicación GPS inválidos"
        if details:
            message += f": {details}"
        super().__init__(message)


class VehicleCapacityExceeded(VehicleException):
    """Capacidad del vehículo excedida."""
    
    def __init__(self, capacity_type: str, requested: str, available: str):
        super().__init__(
            f"Capacidad de {capacity_type} excedida. "
            f"Solicitado: {requested}, Disponible: {available}"
        )


class MaintenanceRecordNotFound(VehicleException):
    """Registro de mantenimiento no encontrado."""
    
    def __init__(self, record_id: str):
        super().__init__(f"Registro de mantenimiento {record_id} no encontrado")


class InvalidVehicleSpecifications(VehicleException):
    """Especificaciones de vehículo inválidas."""
    pass


class VehicleRegistrationExpired(VehicleException):
    """Registro del vehículo expirado."""
    
    def __init__(self, vehicle_id: str, expiry_date: str):
        super().__init__(
            f"Registro del vehículo {vehicle_id} expiró el {expiry_date}"
        )


class VehicleInsuranceExpired(VehicleException):
    """Seguro del vehículo expirado."""
    
    def __init__(self, vehicle_id: str, expiry_date: str):
        super().__init__(
            f"Seguro del vehículo {vehicle_id} expiró el {expiry_date}"
        )
