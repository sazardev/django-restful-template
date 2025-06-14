"""
Vehicle Serializers.
Serializadores para el sistema de vehículos.
"""

from rest_framework import serializers
from decimal import Decimal
from django.db.models import Sum

from apps.vehicles.infrastructure.models import (
    Vehicle, VehicleLocation, MaintenanceRecord, VehicleDocument
)
from apps.vehicles.application.dtos import (
    VehicleCreateDTO, VehicleUpdateDTO, VehicleSpecificationsDTO,
    GPSLocationDTO, MaintenanceRecordDTO
)


class VehicleSpecificationsSerializer(serializers.Serializer):
    """Serializador para especificaciones de vehículo."""
    
    max_weight_kg = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    max_volume_m3 = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    fuel_type = serializers.ChoiceField(choices=Vehicle.FUEL_TYPES)
    fuel_capacity_liters = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=0.01, required=False, allow_null=True
    )
    engine_power_hp = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    transmission_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    emissions_standard = serializers.CharField(max_length=50, required=False, allow_blank=True)


class GPSLocationSerializer(serializers.Serializer):
    """Serializador para ubicación GPS."""
    
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, min_value=-90, max_value=90)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, min_value=-180, max_value=180)
    accuracy_meters = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    altitude_meters = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True
    )
    timestamp = serializers.DateTimeField(required=False, allow_null=True)


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    """Serializador para registros de mantenimiento."""
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'id', 'vehicle', 'maintenance_type', 'description', 'cost',
            'performed_at', 'next_maintenance_date', 'mileage_km',
            'performed_by', 'workshop', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_cost(self, value):
        """Validar que el costo sea positivo."""
        if value < 0:
            raise serializers.ValidationError("El costo debe ser mayor o igual a 0")
        return value


class VehicleDocumentSerializer(serializers.ModelSerializer):
    """Serializador para documentos de vehículo."""
    
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = VehicleDocument
        fields = [
            'id', 'vehicle', 'document_type', 'name', 'description',
            'file', 'issue_date', 'expiry_date', 'is_active',
            'is_expired', 'days_until_expiry', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_expired', 'days_until_expiry']


class VehicleSerializer(serializers.ModelSerializer):
    """Serializador principal para vehículos."""
    
    specifications = VehicleSpecificationsSerializer(source='*', read_only=True)
    current_location = GPSLocationSerializer(read_only=True)
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    
    # Campos calculados
    is_available = serializers.ReadOnlyField()
    needs_maintenance = serializers.ReadOnlyField()
    
    # Información del propietario y conductor
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    current_driver_name = serializers.CharField(source='current_driver.get_full_name', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'brand', 'model', 'year', 'color',
            'vehicle_type', 'vin_number', 'status', 'current_driver',
            'owner', 'specifications', 'registration_expiry', 'insurance_expiry',
            'total_mileage_km', 'last_maintenance_date', 'current_location',
            'maintenance_records', 'documents', 'is_available', 'needs_maintenance',
            'owner_name', 'current_driver_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_available', 'needs_maintenance',
            'owner_name', 'current_driver_name'
        ]

    def to_representation(self, instance):
        """Personalizar la representación del vehículo."""
        data = super().to_representation(instance)
        
        # Agregar especificaciones como un objeto anidado
        data['specifications'] = {
            'max_weight_kg': instance.max_weight_kg,
            'max_volume_m3': instance.max_volume_m3,
            'fuel_type': instance.fuel_type,
            'fuel_capacity_liters': instance.fuel_capacity_liters,
            'engine_power_hp': instance.engine_power_hp,
            'transmission_type': instance.transmission_type,
            'emissions_standard': instance.emissions_standard,
        }
        
        # Agregar ubicación actual si existe
        try:
            latest_location = instance.locations.latest('created_at')
            data['current_location'] = {
                'latitude': latest_location.latitude,
                'longitude': latest_location.longitude,
                'accuracy_meters': latest_location.accuracy_meters,
                'altitude_meters': latest_location.altitude_meters,
                'timestamp': latest_location.created_at,
            }
        except VehicleLocation.DoesNotExist:
            data['current_location'] = None
        
        return data


class VehicleCreateSerializer(serializers.Serializer):
    """Serializador para crear vehículos."""
    
    license_plate = serializers.CharField(max_length=20)
    brand = serializers.CharField(max_length=50)
    model = serializers.CharField(max_length=50)
    year = serializers.IntegerField(min_value=1900, max_value=2030)
    color = serializers.CharField(max_length=30)
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VEHICLE_TYPES)
    vin_number = serializers.CharField(max_length=17, required=False, allow_blank=True)
    specifications = VehicleSpecificationsSerializer()
    owner_id = serializers.UUIDField()
    registration_expiry = serializers.DateTimeField(required=False, allow_null=True)
    insurance_expiry = serializers.DateTimeField(required=False, allow_null=True)
    current_location = GPSLocationSerializer(required=False, allow_null=True)

    def validate_license_plate(self, value):
        """Validar que la placa sea única."""
        if Vehicle.objects.filter(license_plate=value.upper()).exists():
            raise serializers.ValidationError("Ya existe un vehículo con esta placa")
        return value.upper()

    def validate_vin_number(self, value):
        """Validar número VIN."""
        if value and len(value) != 17:
            raise serializers.ValidationError("El número VIN debe tener exactamente 17 caracteres")
        return value

    def to_dto(self) -> VehicleCreateDTO:
        """Convertir a DTO."""
        validated_data = self.validated_data
        
        specifications_dto = VehicleSpecificationsDTO(
            max_weight_kg=validated_data['specifications']['max_weight_kg'],
            max_volume_m3=validated_data['specifications']['max_volume_m3'],
            fuel_type=validated_data['specifications']['fuel_type'],
            fuel_capacity_liters=validated_data['specifications'].get('fuel_capacity_liters'),
            engine_power_hp=validated_data['specifications'].get('engine_power_hp'),
            transmission_type=validated_data['specifications'].get('transmission_type', ''),
            emissions_standard=validated_data['specifications'].get('emissions_standard', '')
        )
        
        current_location_dto = None
        if validated_data.get('current_location'):
            current_location_dto = GPSLocationDTO(
                latitude=validated_data['current_location']['latitude'],
                longitude=validated_data['current_location']['longitude'],
                accuracy_meters=validated_data['current_location'].get('accuracy_meters'),
                altitude_meters=validated_data['current_location'].get('altitude_meters'),
                timestamp=validated_data['current_location'].get('timestamp')
            )
        
        return VehicleCreateDTO(
            license_plate=validated_data['license_plate'],
            brand=validated_data['brand'],
            model=validated_data['model'],
            year=validated_data['year'],
            color=validated_data['color'],
            vehicle_type=validated_data['vehicle_type'],
            specifications=specifications_dto,
            owner_id=validated_data['owner_id'],
            vin_number=validated_data.get('vin_number'),
            registration_expiry=validated_data.get('registration_expiry'),
            insurance_expiry=validated_data.get('insurance_expiry'),
            current_location=current_location_dto
        )


class VehicleUpdateSerializer(serializers.Serializer):
    """Serializador para actualizar vehículos."""
    
    color = serializers.CharField(max_length=30, required=False)
    specifications = VehicleSpecificationsSerializer(required=False)
    status = serializers.ChoiceField(choices=Vehicle.VEHICLE_STATUS, required=False)
    current_location = GPSLocationSerializer(required=False, allow_null=True)
    registration_expiry = serializers.DateTimeField(required=False, allow_null=True)
    insurance_expiry = serializers.DateTimeField(required=False, allow_null=True)
    total_mileage_km = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )

    def to_dto(self) -> VehicleUpdateDTO:
        """Convertir a DTO."""
        validated_data = self.validated_data
        
        specifications_dto = None
        if validated_data.get('specifications'):
            specifications_dto = VehicleSpecificationsDTO(
                max_weight_kg=validated_data['specifications']['max_weight_kg'],
                max_volume_m3=validated_data['specifications']['max_volume_m3'],
                fuel_type=validated_data['specifications']['fuel_type'],
                fuel_capacity_liters=validated_data['specifications'].get('fuel_capacity_liters'),
                engine_power_hp=validated_data['specifications'].get('engine_power_hp'),
                transmission_type=validated_data['specifications'].get('transmission_type', ''),
                emissions_standard=validated_data['specifications'].get('emissions_standard', '')
            )
        
        current_location_dto = None
        if validated_data.get('current_location'):
            current_location_dto = GPSLocationDTO(
                latitude=validated_data['current_location']['latitude'],
                longitude=validated_data['current_location']['longitude'],
                accuracy_meters=validated_data['current_location'].get('accuracy_meters'),
                altitude_meters=validated_data['current_location'].get('altitude_meters'),
                timestamp=validated_data['current_location'].get('timestamp')
            )
        
        return VehicleUpdateDTO(
            color=validated_data.get('color'),
            specifications=specifications_dto,
            status=validated_data.get('status'),
            current_location=current_location_dto,
            registration_expiry=validated_data.get('registration_expiry'),
            insurance_expiry=validated_data.get('insurance_expiry'),
            total_mileage_km=validated_data.get('total_mileage_km')
        )


class VehicleLocationSerializer(serializers.ModelSerializer):
    """Serializador para ubicaciones de vehículos."""
    
    vehicle_info = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleLocation
        fields = [
            'id', 'vehicle', 'latitude', 'longitude', 'accuracy_meters',
            'altitude_meters', 'speed_kmh', 'heading_degrees', 'vehicle_info',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'vehicle_info']

    def get_vehicle_info(self, obj):
        """Obtener información básica del vehículo."""
        return {
            'license_plate': obj.vehicle.license_plate,
            'brand': obj.vehicle.brand,
            'model': obj.vehicle.model,
            'status': obj.vehicle.status
        }

    def validate(self, data):
        """Validaciones personalizadas."""
        if data['latitude'] < -90 or data['latitude'] > 90:
            raise serializers.ValidationError("Latitud debe estar entre -90 y 90")
        
        if data['longitude'] < -180 or data['longitude'] > 180:
            raise serializers.ValidationError("Longitud debe estar entre -180 y 180")
        
        if data.get('accuracy_meters') and data['accuracy_meters'] < 0:
            raise serializers.ValidationError("La precisión no puede ser negativa")
        
        return data


class VehicleAssignmentSerializer(serializers.Serializer):
    """Serializador para asignación de conductores."""
    
    vehicle_id = serializers.UUIDField()
    driver_id = serializers.UUIDField()

    def validate_vehicle_id(self, value):
        """Validar que el vehículo existe."""
        try:
            vehicle = Vehicle.objects.get(id=value)
            if vehicle.status != 'available':
                raise serializers.ValidationError("El vehículo no está disponible")
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError("Vehículo no encontrado")
        return value


class VehicleMaintenanceSerializer(serializers.Serializer):
    """Serializador para mantenimiento de vehículos."""
    
    vehicle_id = serializers.UUIDField()
    maintenance_type = serializers.ChoiceField(choices=MaintenanceRecord.MAINTENANCE_TYPES)
    description = serializers.CharField()
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    scheduled_date = serializers.DateTimeField(required=False, allow_null=True)
    performed_at = serializers.DateTimeField(required=False, allow_null=True)
    mileage_km = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    performed_by = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class VehicleFilterSerializer(serializers.Serializer):
    """Serializador para filtros de vehículos."""
    
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VEHICLE_TYPES, required=False)
    status = serializers.ChoiceField(choices=Vehicle.VEHICLE_STATUS, required=False)
    owner_id = serializers.UUIDField(required=False)
    brand = serializers.CharField(max_length=50, required=False)
    model = serializers.CharField(max_length=50, required=False)
    year_from = serializers.IntegerField(min_value=1900, required=False)
    year_to = serializers.IntegerField(max_value=2030, required=False)
    min_weight_capacity = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )
    max_weight_capacity = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )
    min_volume_capacity = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )
    max_volume_capacity = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )
    fuel_type = serializers.ChoiceField(choices=Vehicle.FUEL_TYPES, required=False)
    maintenance_due = serializers.BooleanField(required=False)
    available_only = serializers.BooleanField(required=False)
    current_driver_id = serializers.UUIDField(required=False)
    registration_expiring_days = serializers.IntegerField(min_value=0, required=False)
    insurance_expiring_days = serializers.IntegerField(min_value=0, required=False)


class VehicleAnalyticsSerializer(serializers.Serializer):
    """Serializador para análisis de vehículos."""
    
    vehicle_id = serializers.UUIDField(required=False)
    owner_id = serializers.UUIDField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    metrics_type = serializers.ChoiceField(
        choices=['utilization', 'performance', 'maintenance_costs', 'fleet_summary'],
        default='utilization'
    )


# Alias para compatibilidad con views
CreateVehicleSerializer = VehicleCreateSerializer
UpdateVehicleSerializer = VehicleUpdateSerializer


class VehicleListSerializer(serializers.ModelSerializer):
    """Serializador simplificado para listado de vehículos."""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    current_driver_name = serializers.CharField(source='current_driver.get_full_name', read_only=True)
    is_available = serializers.ReadOnlyField()
    needs_maintenance = serializers.ReadOnlyField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'brand', 'model', 'year', 'color',
            'vehicle_type', 'status', 'owner_name', 'current_driver_name',
            'total_mileage_km', 'is_available', 'needs_maintenance',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner_name', 'current_driver_name', 'is_available',
            'needs_maintenance', 'created_at', 'updated_at'
        ]


class VehicleDetailSerializer(VehicleSerializer):
    """Serializador detallado para vehículos con toda la información."""
    
    recent_locations = serializers.SerializerMethodField()
    maintenance_summary = serializers.SerializerMethodField()
    compliance_status = serializers.SerializerMethodField()
    
    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + [
            'recent_locations', 'maintenance_summary', 'compliance_status'
        ]
    
    def get_recent_locations(self, obj):
        """Obtener las últimas 5 ubicaciones del vehículo."""
        recent_locations = obj.locations.order_by('-created_at')[:5]
        return VehicleLocationSerializer(recent_locations, many=True).data
    
    def get_maintenance_summary(self, obj):
        """Obtener resumen de mantenimiento."""
        maintenance_records = obj.maintenance_records.order_by('-performed_at')[:5]
        total_cost = maintenance_records.aggregate(
            total=Sum('cost')
        )['total'] or 0
        
        return {
            'total_records': obj.maintenance_records.count(),
            'recent_records': MaintenanceRecordSerializer(maintenance_records, many=True).data,
            'total_cost_last_year': total_cost,
            'last_maintenance': maintenance_records.first().performed_at if maintenance_records.exists() else None
        }
    
    def get_compliance_status(self, obj):
        """Obtener estado de cumplimiento."""
        from datetime import datetime, timedelta
        now = datetime.now().date()
        
        registration_status = 'unknown'
        insurance_status = 'unknown'
        
        if obj.registration_expiry:
            days_to_reg_expiry = (obj.registration_expiry.date() - now).days
            if days_to_reg_expiry < 0:
                registration_status = 'expired'
            elif days_to_reg_expiry <= 30:
                registration_status = 'expiring_soon'
            else:
                registration_status = 'valid'
        
        if obj.insurance_expiry:
            days_to_ins_expiry = (obj.insurance_expiry.date() - now).days
            if days_to_ins_expiry < 0:
                insurance_status = 'expired'
            elif days_to_ins_expiry <= 30:
                insurance_status = 'expiring_soon'
            else:
                insurance_status = 'valid'
        
        return {
            'registration_status': registration_status,
            'insurance_status': insurance_status,
            'registration_expiry': obj.registration_expiry,
            'insurance_expiry': obj.insurance_expiry,
            'overall_compliance': 'compliant' if registration_status == 'valid' and insurance_status == 'valid' else 'non_compliant'
        }


class VehicleBulkActionSerializer(serializers.Serializer):
    """Serializador para acciones en lote sobre vehículos."""
    
    vehicle_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    action = serializers.ChoiceField(choices=[
        ('activate', 'Activar'),
        ('deactivate', 'Desactivar'),
        ('assign_driver', 'Asignar conductor'),
        ('unassign_driver', 'Desasignar conductor'),
        ('schedule_maintenance', 'Programar mantenimiento'),
        ('update_status', 'Actualizar estado'),
        ('export', 'Exportar'),
        ('delete', 'Eliminar')
    ])
    action_params = serializers.JSONField(required=False, default=dict)
    
    def validate_vehicle_ids(self, value):
        """Validar que todos los vehículos existen."""
        existing_ids = set(Vehicle.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(
                f"Los siguientes vehículos no existen: {list(missing_ids)}"
            )
        
        return value
    
    def validate(self, data):
        """Validaciones específicas por acción."""
        action = data.get('action')
        action_params = data.get('action_params', {})
        
        if action == 'assign_driver' and 'driver_id' not in action_params:
            raise serializers.ValidationError(
                "Para asignar conductor se requiere 'driver_id' en action_params"
            )
        
        if action == 'update_status' and 'status' not in action_params:
            raise serializers.ValidationError(
                "Para actualizar estado se requiere 'status' en action_params"
            )
        
        if action == 'schedule_maintenance':
            required_fields = ['maintenance_type', 'scheduled_date']
            missing_fields = [field for field in required_fields if field not in action_params]
            if missing_fields:
                raise serializers.ValidationError(
                    f"Para programar mantenimiento se requieren: {missing_fields}"
                )
        
        return data


class VehicleSearchSerializer(serializers.Serializer):
    """Serializador para búsqueda avanzada de vehículos."""
    
    query = serializers.CharField(max_length=200, required=False, allow_blank=True)
    filters = VehicleFilterSerializer(required=False)
    sort_by = serializers.ChoiceField(
        choices=[
            ('license_plate', 'Placa'),
            ('brand', 'Marca'),
            ('model', 'Modelo'),
            ('year', 'Año'),
            ('created_at', 'Fecha de creación'),
            ('total_mileage_km', 'Kilometraje'),
            ('status', 'Estado')
        ],
        required=False,
        default='license_plate'
    )
    sort_direction = serializers.ChoiceField(
        choices=[('asc', 'Ascendente'), ('desc', 'Descendente')],
        default='asc'
    )
    include_inactive = serializers.BooleanField(default=False)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)


class VehicleSummarySerializer(serializers.ModelSerializer):
    """Serializer resumido para vehículo."""
    
    type_name = serializers.CharField(source='type.name', read_only=True)
    location_address = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'make', 'model', 'year', 'type_name',
            'license_plate', 'status', 'mileage', 'condition',
            'location_address', 'main_image'
        ]
        read_only_fields = fields
    
    def get_location_address(self, obj):
        """Obtener dirección de ubicación actual."""
        current_location = obj.locations.filter(is_current=True).first()
        if current_location:
            return current_location.address
        return None
    
    def get_main_image(self, obj):
        """Obtener imagen principal del vehículo."""
        first_image = obj.images.first()
        if first_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None
