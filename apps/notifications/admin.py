"""
Notification Admin Configuration.
Configuración del panel administrativo para notificaciones.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.notifications.infrastructure.models import (
    NotificationModel, NotificationChannelModel, NotificationTemplateModel,
    NotificationDeliveryModel
)


@admin.register(NotificationModel)
class NotificationAdmin(admin.ModelAdmin):
    """Admin para notificaciones."""
    
    list_display = [
        'title', 'user_email', 'notification_type', 'priority_badge',
        'status_badge', 'is_read', 'created_at', 'expires_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'status', 'is_read',
        'created_at', 'expires_at'
    ]
    search_fields = ['title', 'message', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información General', {
            'fields': ('id', 'user', 'title', 'message')
        }),
        ('Configuración', {
            'fields': ('notification_type', 'priority', 'status', 'data')
        }),
        ('Estado', {
            'fields': ('is_read', 'read_at', 'expires_at')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Mostrar email del usuario."""
        return obj.user.email
    user_email.short_description = 'Usuario'
    user_email.admin_order_field = 'user__email'
    
    def priority_badge(self, obj):
        """Mostrar prioridad con badge."""
        colors = {
            1: 'success',  # Low
            2: 'info',     # Normal
            3: 'warning',  # High
            4: 'danger',   # Urgent
            5: 'dark',     # Critical
        }
        color = colors.get(obj.priority, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'
    priority_badge.admin_order_field = 'priority'
    
    def status_badge(self, obj):
        """Mostrar estado con badge."""
        colors = {
            'pending': 'warning',
            'sent': 'info',
            'delivered': 'success',
            'read': 'primary',
            'failed': 'danger',
            'expired': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related(
            'user', 'created_by'
        )
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_expired']
    
    def mark_as_read(self, request, queryset):
        """Acción para marcar como leídas."""
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
            status='read'
        )
        self.message_user(request, f'{updated} notificaciones marcadas como leídas.')
    mark_as_read.short_description = 'Marcar como leídas'
    
    def mark_as_unread(self, request, queryset):
        """Acción para marcar como no leídas."""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None,
            status='sent'
        )
        self.message_user(request, f'{updated} notificaciones marcadas como no leídas.')
    mark_as_unread.short_description = 'Marcar como no leídas'
    
    def delete_expired(self, request, queryset):
        """Acción para eliminar expiradas."""
        now = timezone.now()
        expired = queryset.filter(expires_at__lt=now)
        count = expired.count()
        expired.delete()
        self.message_user(request, f'{count} notificaciones expiradas eliminadas.')
    delete_expired.short_description = 'Eliminar expiradas'


@admin.register(NotificationChannelModel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Admin para canales de notificación."""
    
    list_display = [
        'user_email', 'channel_type', 'channel_identifier',
        'is_active', 'is_verified', 'created_at', 'last_used_at'
    ]
    list_filter = ['channel_type', 'is_active', 'is_verified', 'created_at']
    search_fields = ['user__email', 'channel_identifier']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_used_at']
    
    fieldsets = (
        ('Información del Canal', {
            'fields': ('user', 'channel_type', 'channel_identifier')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_verified', 'settings')
        }),
        ('Actividad', {
            'fields': ('created_at', 'updated_at', 'last_used_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Mostrar email del usuario."""
        return obj.user.email
    user_email.short_description = 'Usuario'
    user_email.admin_order_field = 'user__email'
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('user')


@admin.register(NotificationTemplateModel)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin para plantillas de notificación."""
    
    list_display = [
        'name', 'notification_type', 'default_priority',
        'is_active', 'created_at', 'usage_count'
    ]
    list_filter = ['notification_type', 'default_priority', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'title_template', 'message_template']
    readonly_fields = ['id', 'created_at', 'updated_at', 'usage_count']
    
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Configuración', {
            'fields': ('notification_type', 'default_priority', 'default_channels')
        }),
        ('Plantillas', {
            'fields': ('title_template', 'message_template')
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at', 'usage_count'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_count(self, obj):
        """Mostrar cantidad de usos de la plantilla."""
        # TODO: Implementar contador de uso cuando se agregue la funcionalidad
        return "N/A"
    usage_count.short_description = 'Usos'
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('created_by')


@admin.register(NotificationDeliveryModel)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    """Admin para entregas de notificación."""
    
    list_display = [
        'notification_title', 'channel_info', 'status_badge',
        'attempts', 'sent_at', 'delivered_at'
    ]
    list_filter = ['status', 'channel__channel_type', 'sent_at', 'delivered_at']
    search_fields = [
        'notification__title', 'channel__channel_identifier',
        'notification__user__email'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sent_at', 'delivered_at'
    ]
    
    fieldsets = (
        ('Entrega', {
            'fields': ('notification', 'channel', 'status')
        }),
        ('Datos', {
            'fields': ('delivery_data', 'error_message', 'attempts')
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def notification_title(self, obj):
        """Mostrar título de la notificación."""
        return obj.notification.title
    notification_title.short_description = 'Notificación'
    notification_title.admin_order_field = 'notification__title'
    
    def channel_info(self, obj):
        """Mostrar información del canal."""
        return f"{obj.channel.channel_type}: {obj.channel.channel_identifier}"
    channel_info.short_description = 'Canal'
    
    def status_badge(self, obj):
        """Mostrar estado con badge."""
        colors = {
            'pending': 'warning',
            'sent': 'info',
            'delivered': 'success',
            'read': 'primary',
            'failed': 'danger',
            'expired': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related(
            'notification', 'notification__user', 'channel'
        )


# Configuración adicional del admin
admin.site.site_header = "Sistema de Notificaciones - Administración"
admin.site.site_title = "Notificaciones Admin"
admin.site.index_title = "Panel de Administración de Notificaciones"
