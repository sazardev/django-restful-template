"""
Vehicle Admin Configuration.
Configuración del panel administrativo para vehículos.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from datetime import datetime, timedelta

from .infrastructure.models import Vehicle, VehicleLocation, MaintenanceRecord, VehicleDocument


class MaintenanceRecordInline(admin.TabularInline):
    """Inline para registros de mantenimiento."""
    model = MaintenanceRecord
    extra = 0
    readonly_fields = ['created_at']
    fields = [
        'maintenance_type', 'description', 'cost', 'performed_at',
        'performed_by', 'workshop', 'created_at'
    ]
    ordering = ['-performed_at']


class VehicleDocumentInline(admin.TabularInline):
    """Inline para documentos de vehículo."""
    model = VehicleDocument
    extra = 0
    readonly_fields = ['created_at', 'is_expired', 'days_until_expiry']
    fields = [
        'document_type', 'name', 'file', 'issue_date', 'expiry_date',
        'is_active', 'is_expired', 'days_until_expiry'
    ]


class VehicleLocationInline(admin.TabularInline):
    """Inline para ubicaciones de vehículo."""
    model = VehicleLocation
    extra = 0
    readonly_fields = ['created_at']
    fields = ['latitude', 'longitude', 'accuracy_meters', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Mostrar solo las últimas 5 ubicaciones."""
        return super().get_queryset(request)[:5]


class VehicleStatusFilter(SimpleListFilter):
    """Filtro personalizado por estado de vehículo."""
    title = 'estado'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return Vehicle.VEHICLE_STATUS

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class MaintenanceDueFilter(SimpleListFilter):
    """Filtro para vehículos que necesitan mantenimiento."""
    title = 'mantenimiento debido'
    parameter_name = 'maintenance_due'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Sí'),
            ('no', 'No'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            # Vehículos sin mantenimiento o con más de 6 meses
            six_months_ago = datetime.now() - timedelta(days=180)
            return queryset.filter(
                Q(last_maintenance_date__isnull=True) |
                Q(last_maintenance_date__lt=six_months_ago)
            )
        elif self.value() == 'no':
            six_months_ago = datetime.now() - timedelta(days=180)
            return queryset.filter(
                last_maintenance_date__gte=six_months_ago
            )
        return queryset


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Administrador para vehículos."""
    
    list_display = [
        'license_plate', 'brand_model', 'year', 'vehicle_type',
        'status_badge', 'owner', 'current_driver', 'maintenance_status',
        'total_mileage_km', 'created_at'
    ]
    list_filter = [
        VehicleStatusFilter, 'vehicle_type', 'fuel_type', 'year',
        MaintenanceDueFilter, 'created_at'
    ]
    search_fields = [
        'license_plate', 'brand', 'model', 'vin_number',
        'owner__first_name', 'owner__last_name', 'owner__email'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'is_available',
        'needs_maintenance', 'current_location_link'
    ]
    
    fieldsets = [
        ('Información Básica', {
            'fields': [
                'license_plate', 'brand', 'model', 'year', 'color',
                'vehicle_type', 'vin_number'
            ]
        }),
        ('Estado y Asignación', {
            'fields': [
                'status', 'current_driver', 'owner', 'is_available'
            ]
        }),
        ('Especificaciones Técnicas', {
            'fields': [
                'max_weight_kg', 'max_volume_m3', 'fuel_type',
                'fuel_capacity_liters', 'engine_power_hp',
                'transmission_type', 'emissions_standard'
            ]
        }),
        ('Documentación', {
            'fields': [
                'registration_expiry', 'insurance_expiry'
            ]
        }),
        ('Métricas', {
            'fields': [
                'total_mileage_km', 'last_maintenance_date',
                'needs_maintenance'
            ]
        }),
        ('Ubicación', {
            'fields': ['current_location_link']
        }),
        ('Metadatos', {
            'fields': ['id', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    inlines = [MaintenanceRecordInline, VehicleDocumentInline, VehicleLocationInline]
    
    actions = [
        'mark_as_available', 'mark_as_maintenance', 'mark_as_out_of_service',
        'export_to_csv'
    ]
    
    def brand_model(self, obj):
        """Mostrar marca y modelo juntos."""
        return f"{obj.brand} {obj.model}"
    brand_model.short_description = 'Marca/Modelo'
    brand_model.admin_order_field = 'brand'
    
    def status_badge(self, obj):
        """Mostrar estado con color."""
        colors = {
            'available': 'green',
            'in_use': 'blue',
            'maintenance': 'orange',
            'out_of_service': 'red',
            'retired': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def maintenance_status(self, obj):
        """Mostrar estado de mantenimiento."""
        if obj.needs_maintenance:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ Requiere</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Al día</span>'
        )
    maintenance_status.short_description = 'Mantenimiento'
    maintenance_status.admin_order_field = 'last_maintenance_date'
    
    def current_location_link(self, obj):
        """Link a la ubicación actual."""
        try:
            location = obj.locations.latest('created_at')
            return format_html(
                '<a href="https://maps.google.com/maps?q={},{}" target="_blank">'
                'Ver en mapa ({}, {})</a>',
                location.latitude, location.longitude,
                location.latitude, location.longitude
            )
        except VehicleLocation.DoesNotExist:
            return "Sin ubicación"
    current_location_link.short_description = 'Ubicación Actual'
    
    def mark_as_available(self, request, queryset):
        """Marcar vehículos como disponibles."""
        updated = queryset.update(status='available', current_driver=None)
        self.message_user(
            request,
            f'{updated} vehículo(s) marcado(s) como disponible(s).'
        )
    mark_as_available.short_description = "Marcar como disponible"
    
    def mark_as_maintenance(self, request, queryset):
        """Marcar vehículos en mantenimiento."""
        updated = queryset.update(status='maintenance', current_driver=None)
        self.message_user(
            request,
            f'{updated} vehículo(s) marcado(s) en mantenimiento.'
        )
    mark_as_maintenance.short_description = "Marcar en mantenimiento"
    
    def mark_as_out_of_service(self, request, queryset):
        """Marcar vehículos fuera de servicio."""
        updated = queryset.update(status='out_of_service', current_driver=None)
        self.message_user(
            request,
            f'{updated} vehículo(s) marcado(s) fuera de servicio.'
        )
    mark_as_out_of_service.short_description = "Marcar fuera de servicio"
    
    def export_to_csv(self, request, queryset):
        """Exportar vehículos a CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="vehicles.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Placa', 'Marca', 'Modelo', 'Año', 'Tipo', 'Estado',
            'Propietario', 'Conductor', 'Kilometraje'
        ])
        
        for vehicle in queryset:
            writer.writerow([
                vehicle.license_plate,
                vehicle.brand,
                vehicle.model,
                vehicle.year,
                vehicle.get_vehicle_type_display(),
                vehicle.get_status_display(),
                vehicle.owner.get_full_name() if vehicle.owner else '',
                vehicle.current_driver.get_full_name() if vehicle.current_driver else '',
                vehicle.total_mileage_km
            ])
        
        return response
    export_to_csv.short_description = "Exportar a CSV"
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related(
            'owner', 'current_driver'
        ).prefetch_related('maintenance_records', 'locations')


@admin.register(VehicleLocation)
class VehicleLocationAdmin(admin.ModelAdmin):
    """Administrador para ubicaciones de vehículos."""
    
    list_display = [
        'vehicle', 'latitude', 'longitude', 'accuracy_meters',
        'created_at', 'map_link'
    ]
    list_filter = ['created_at', 'vehicle__vehicle_type']
    search_fields = ['vehicle__license_plate', 'vehicle__brand', 'vehicle__model']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'map_link']
    
    def map_link(self, obj):
        """Link al mapa."""
        return format_html(
            '<a href="https://maps.google.com/maps?q={},{}" target="_blank">'
            'Ver en Google Maps</a>',
            obj.latitude, obj.longitude
        )
    map_link.short_description = 'Mapa'


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    """Administrador para registros de mantenimiento."""
    
    list_display = [
        'vehicle', 'maintenance_type', 'cost', 'performed_at',
        'performed_by', 'workshop'
    ]
    list_filter = [
        'maintenance_type', 'performed_at', 'vehicle__vehicle_type'
    ]
    search_fields = [
        'vehicle__license_plate', 'description', 'performed_by', 'workshop'
    ]
    ordering = ['-performed_at']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Información del Mantenimiento', {
            'fields': [
                'vehicle', 'maintenance_type', 'description', 'cost'
            ]
        }),
        ('Fechas', {
            'fields': [
                'performed_at', 'next_maintenance_date'
            ]
        }),
        ('Detalles', {
            'fields': [
                'mileage_km', 'performed_by', 'workshop', 'notes'
            ]
        }),
        ('Archivos', {
            'fields': [
                'invoice_file', 'receipt_file'
            ]
        }),
        ('Metadatos', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('vehicle')


@admin.register(VehicleDocument)
class VehicleDocumentAdmin(admin.ModelAdmin):
    """Administrador para documentos de vehículos."""
    
    list_display = [
        'vehicle', 'document_type', 'name', 'expiry_date',
        'expiry_status', 'is_active'
    ]
    list_filter = [
        'document_type', 'is_active', 'expiry_date', 'created_at'
    ]
    search_fields = [
        'vehicle__license_plate', 'name', 'description'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'is_expired', 'days_until_expiry']
    
    def expiry_status(self, obj):
        """Estado de vencimiento."""
        if not obj.expiry_date:
            return "N/A"
        
        days = obj.days_until_expiry
        if days is None:
            return "N/A"
        elif days < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">Vencido</span>'
            )
        elif days <= 30:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Por vencer</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">Vigente</span>'
            )
    expiry_status.short_description = 'Estado'
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('vehicle')


# Personalización del sitio admin
admin.site.site_header = "Django RESTful Template - Administración"
admin.site.site_title = "Administración"
admin.site.index_title = "Panel de Administración"
