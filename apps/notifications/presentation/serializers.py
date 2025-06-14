"""
Notification Presentation Serializers.
Serializadores para la presentación de notificaciones.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.notifications.domain.entities import NotificationType, NotificationPriority
from apps.notifications.infrastructure.models import (
    NotificationModel, NotificationChannelModel, NotificationTemplateModel
)

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializador para notificaciones."""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_since_created = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationModel
        fields = [
            'id', 'title', 'message', 'notification_type', 'notification_type_display',
            'priority', 'priority_display', 'status', 'status_display', 'data',
            'is_read', 'created_at', 'read_at', 'expires_at', 'time_since_created',
            'is_expired'
        ]
        read_only_fields = [
            'id', 'created_at', 'read_at', 'notification_type_display',
            'priority_display', 'status_display', 'time_since_created', 'is_expired'
        ]
    
    def get_time_since_created(self, obj):
        """Obtener tiempo transcurrido desde creación."""
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        if obj.created_at:
            return timesince(obj.created_at, timezone.now())
        return None
    
    def get_is_expired(self, obj):
        """Verificar si la notificación está expirada."""
        return obj.is_expired()


class NotificationCreateSerializer(serializers.Serializer):
    """Serializador para crear notificaciones."""
    
    user_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(
        choices=[(t.value, t.value) for t in NotificationType],
        default=NotificationType.INFO.value
    )
    priority = serializers.ChoiceField(
        choices=[(p.value, str(p.value)) for p in NotificationPriority],
        default=NotificationPriority.NORMAL.value
    )
    data = serializers.JSONField(required=False, default=dict)
    expires_in_hours = serializers.IntegerField(required=False, min_value=1, max_value=8760)  # máximo 1 año
    send_realtime = serializers.BooleanField(default=True)
    
    def validate_user_id(self, value):
        """Validar que el usuario existe."""
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")


class NotificationListSerializer(serializers.Serializer):
    """Serializador para lista de notificaciones con paginación."""
    
    notifications = NotificationSerializer(many=True, read_only=True)
    total_count = serializers.IntegerField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    has_next = serializers.BooleanField(read_only=True)
    has_previous = serializers.BooleanField(read_only=True)


class NotificationFilterSerializer(serializers.Serializer):
    """Serializador para filtros de notificaciones."""
    
    unread_only = serializers.BooleanField(default=False)
    notification_type = serializers.ChoiceField(
        choices=[(t.value, t.value) for t in NotificationType],
        required=False,
        allow_blank=True
    )
    priority = serializers.ChoiceField(
        choices=[(p.value, str(p.value)) for p in NotificationPriority],
        required=False,
        allow_blank=True
    )
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)
    offset = serializers.IntegerField(default=0, min_value=0)
    
    def validate(self, data):
        """Validar que date_from sea menor que date_to."""
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] > data['date_to']:
                raise serializers.ValidationError(
                    "La fecha inicial debe ser menor que la fecha final"
                )
        return data


class MarkNotificationsSerializer(serializers.Serializer):
    """Serializador para marcar notificaciones."""
    
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    mark_as_read = serializers.BooleanField(default=True)


class BroadcastNotificationSerializer(serializers.Serializer):
    """Serializador para broadcast de notificaciones."""
    
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(
        choices=[(t.value, t.value) for t in NotificationType],
        default=NotificationType.INFO.value
    )
    priority = serializers.ChoiceField(
        choices=[(p.value, str(p.value)) for p in NotificationPriority],
        default=NotificationPriority.NORMAL.value
    )
    data = serializers.JSONField(required=False, default=dict)
    target_all_users = serializers.BooleanField(default=True)
    target_groups = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    target_user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    expires_in_hours = serializers.IntegerField(required=False, min_value=1, max_value=8760)
    
    def validate(self, data):
        """Validar targets de broadcast."""
        if not data.get('target_all_users'):
            if not data.get('target_groups') and not data.get('target_user_ids'):
                raise serializers.ValidationError(
                    "Debe especificar grupos o usuarios si no es para todos"
                )
        return data


class NotificationStatsSerializer(serializers.Serializer):
    """Serializador para estadísticas de notificaciones."""
    
    total_notifications = serializers.IntegerField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    read_count = serializers.IntegerField(read_only=True)
    notifications_by_type = serializers.DictField(read_only=True)
    notifications_by_priority = serializers.DictField(read_only=True)
    recent_notifications_count = serializers.IntegerField(read_only=True)


class NotificationChannelSerializer(serializers.ModelSerializer):
    """Serializador para canales de notificación."""
    
    channel_type_display = serializers.CharField(source='get_channel_type_display', read_only=True)
    
    class Meta:
        model = NotificationChannelModel
        fields = [
            'id', 'channel_type', 'channel_type_display', 'channel_identifier',
            'is_active', 'is_verified', 'settings', 'created_at', 'updated_at',
            'last_used_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used_at', 'channel_type_display']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializador para plantillas de notificación."""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_default_priority_display', read_only=True)
    
    class Meta:
        model = NotificationTemplateModel
        fields = [
            'id', 'name', 'description', 'notification_type', 'notification_type_display',
            'title_template', 'message_template', 'default_priority', 'priority_display',
            'default_channels', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'notification_type_display', 'priority_display'
        ]


class NotificationSummarySerializer(serializers.Serializer):
    """Serializador para resumen de notificaciones."""
    
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    notification_type = serializers.CharField(read_only=True)
    priority = serializers.IntegerField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class WebSocketMessageSerializer(serializers.Serializer):
    """Serializador para mensajes WebSocket."""
    
    type = serializers.CharField()
    notification_id = serializers.UUIDField(required=False)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100, required=False)
    offset = serializers.IntegerField(default=0, min_value=0, required=False)
    unread_only = serializers.BooleanField(default=False, required=False)
