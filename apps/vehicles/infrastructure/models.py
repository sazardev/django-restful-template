"""
Vehicle Models.
Modelos de Django para el sistema de vehículos.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

from shared.infrastructure.models import BaseModel

User = get_user_model()


class Vehicle(BaseModel):
    """Modelo de vehículo."""
    
    VEHICLE_TYPES = [
        ('truck', 'Camión'),
        ('van', 'Furgoneta'),
        ('motorcycle', 'Motocicleta'),
        ('car', 'Automóvil'),
        ('trailer', 'Remolque'),
        ('container', 'Contenedor'),
    ]
    
    VEHICLE_STATUS = [
        ('available', 'Disponible'),
        ('in_use', 'En uso'),
        ('maintenance', 'En mantenimiento'),
        ('out_of_service', 'Fuera de servicio'),
        ('retired', 'Retirado'),
    ]
    
    FUEL_TYPES = [
        ('gasoline', 'Gasolina'),
        ('diesel', 'Diésel'),
        ('electric', 'Eléctrico'),
        ('hybrid', 'Híbrido'),
        ('cng', 'Gas Natural Comprimido'),
        ('lpg', 'Gas Licuado de Petróleo'),
    ]

    # Información básica
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Placa"
    )
    brand = models.CharField(max_length=50, verbose_name="Marca")
    model = models.CharField(max_length=50, verbose_name="Modelo")
    year = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2030)
        ],
        verbose_name="Año"
    )
    color = models.CharField(max_length=30, verbose_name="Color")
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPES,
        verbose_name="Tipo de vehículo"
    )
    vin_number = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        verbose_name="Número VIN"
    )

    # Estado y asignación
    status = models.CharField(
        max_length=20,
        choices=VEHICLE_STATUS,
        default='available',
        verbose_name="Estado"
    )
    current_driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_vehicles',
        verbose_name="Conductor actual"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_vehicles',
        verbose_name="Propietario"
    )

    # Especificaciones técnicas
    max_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Peso máximo (kg)"
    )
    max_volume_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Volumen máximo (m³)"
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_TYPES,
        verbose_name="Tipo de combustible"
    )
    fuel_capacity_liters = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Capacidad de combustible (L)"
    )
    engine_power_hp = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Potencia del motor (HP)"
    )
    transmission_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Tipo de transmisión"
    )
    emissions_standard = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Estándar de emisiones"
    )

    # Documentación
    registration_expiry = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Vencimiento de registro"
    )
    insurance_expiry = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Vencimiento de seguro"
    )

    # Métricas
    total_mileage_km = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Kilometraje total"
    )
    last_maintenance_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha último mantenimiento"
    )

    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['license_plate']
        indexes = [
            models.Index(fields=['license_plate']),
            models.Index(fields=['status']),
            models.Index(fields=['vehicle_type']),
            models.Index(fields=['owner']),
            models.Index(fields=['current_driver']),
        ]

    def __str__(self):
        return f"{self.license_plate} - {self.brand} {self.model}"

    def clean(self):
        """Validaciones personalizadas."""
        from django.core.exceptions import ValidationError
        
        if self.license_plate:
            self.license_plate = self.license_plate.upper().strip()
        
        if self.status == 'in_use' and not self.current_driver:
            raise ValidationError({
                'current_driver': 'Un vehículo en uso debe tener un conductor asignado'
            })
        
        if self.status != 'in_use' and self.current_driver:
            raise ValidationError({
                'status': 'Solo los vehículos en uso pueden tener conductor asignado'
            })

    @property
    def is_available(self):
        """Verificar si el vehículo está disponible."""
        return self.status == 'available'

    @property
    def needs_maintenance(self):
        """Verificar si necesita mantenimiento."""
        from datetime import datetime, timedelta
        
        if not self.last_maintenance_date:
            return True
        
        # 6 meses desde último mantenimiento
        maintenance_interval = timedelta(days=180)
        return datetime.now() - self.last_maintenance_date > maintenance_interval


class VehicleLocation(BaseModel):
    """Modelo para ubicaciones de vehículos."""
    
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name="Vehículo"
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        validators=[
            MinValueValidator(Decimal('-90.0')),
            MaxValueValidator(Decimal('90.0'))
        ],
        verbose_name="Latitud"
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        validators=[
            MinValueValidator(Decimal('-180.0')),
            MaxValueValidator(Decimal('180.0'))
        ],
        verbose_name="Longitud"
    )
    accuracy_meters = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Precisión (metros)"
    )
    altitude_meters = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Altitud (metros)"
    )
    speed_kmh = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Velocidad (km/h)"
    )
    heading_degrees = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('360'))
        ],
        verbose_name="Rumbo (grados)"
    )
    
    class Meta:
        db_table = 'vehicle_locations'
        verbose_name = 'Ubicación de vehículo'
        verbose_name_plural = 'Ubicaciones de vehículos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', '-created_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.latitude}, {self.longitude}"


class MaintenanceRecord(BaseModel):
    """Modelo para registros de mantenimiento."""
    
    MAINTENANCE_TYPES = [
        ('preventive', 'Preventivo'),
        ('corrective', 'Correctivo'),
        ('inspection', 'Inspección'),
        ('oil_change', 'Cambio de aceite'),
        ('tire_change', 'Cambio de llantas'),
        ('brake_service', 'Servicio de frenos'),
        ('engine_service', 'Servicio de motor'),
        ('electrical', 'Sistema eléctrico'),
        ('cooling_system', 'Sistema de refrigeración'),
        ('transmission', 'Transmisión'),
        ('other', 'Otro'),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='maintenance_records',
        verbose_name="Vehículo"
    )
    maintenance_type = models.CharField(
        max_length=50,
        choices=MAINTENANCE_TYPES,
        verbose_name="Tipo de mantenimiento"
    )
    description = models.TextField(verbose_name="Descripción")
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Costo"
    )
    performed_at = models.DateTimeField(verbose_name="Fecha de realización")
    next_maintenance_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Próximo mantenimiento"
    )
    mileage_km = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Kilometraje"
    )
    performed_by = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Realizado por"
    )
    workshop = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Taller"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas adicionales"
    )
    
    # Archivos adjuntos
    invoice_file = models.FileField(
        upload_to='maintenance/invoices/',
        null=True,
        blank=True,
        verbose_name="Factura"
    )
    receipt_file = models.FileField(
        upload_to='maintenance/receipts/',
        null=True,
        blank=True,
        verbose_name="Recibo"
    )

    class Meta:
        db_table = 'vehicle_maintenance_records'
        verbose_name = 'Registro de mantenimiento'
        verbose_name_plural = 'Registros de mantenimiento'
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['vehicle', '-performed_at']),
            models.Index(fields=['maintenance_type']),
            models.Index(fields=['performed_at']),
        ]

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.get_maintenance_type_display()} ({self.performed_at.date()})"

    def clean(self):
        """Validaciones personalizadas."""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        if self.performed_at and self.performed_at > timezone.now():
            raise ValidationError({
                'performed_at': 'La fecha de realización no puede ser futura'
            })
        
        if (self.next_maintenance_date and self.performed_at and 
            self.next_maintenance_date <= self.performed_at):
            raise ValidationError({
                'next_maintenance_date': 'La fecha del próximo mantenimiento debe ser posterior a la fecha de realización'
            })


class VehicleDocument(BaseModel):
    """Modelo para documentos de vehículos."""
    
    DOCUMENT_TYPES = [
        ('registration', 'Registro/Tarjeta de circulación'),
        ('insurance', 'Póliza de seguro'),
        ('license', 'Licencia de conducir'),
        ('inspection', 'Verificación/Inspección'),
        ('permit', 'Permiso especial'),
        ('invoice', 'Factura de compra'),
        ('manual', 'Manual del propietario'),
        ('warranty', 'Garantía'),
        ('other', 'Otro'),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Vehículo"
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        verbose_name="Tipo de documento"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre del documento")
    description = models.TextField(blank=True, verbose_name="Descripción")
    file = models.FileField(
        upload_to='vehicles/documents/',
        verbose_name="Archivo"
    )
    issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de emisión"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de vencimiento"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        db_table = 'vehicle_documents'
        verbose_name = 'Documento de vehículo'
        verbose_name_plural = 'Documentos de vehículos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', 'document_type']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.name}"

    @property
    def is_expired(self):
        """Verificar si el documento está vencido."""
        if not self.expiry_date:
            return False
        
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        """Días hasta el vencimiento."""
        if not self.expiry_date:
            return None
        
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days
