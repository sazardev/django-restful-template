"""
Notification Infrastructure Models.
Modelos de infraestructura para notificaciones.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.notifications.domain.entities import (
    NotificationType, NotificationChannel, NotificationStatus, 
    NotificationPriority
)

User = get_user_model()


class NotificationModel(models.Model):
    """Modelo de notificación."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Usuario'
    )
    title = models.CharField(max_length=255, verbose_name='Título')
    message = models.TextField(verbose_name='Mensaje')
    notification_type = models.CharField(
        max_length=20,
        choices=[(t.value, t.value.title()) for t in NotificationType],
        default=NotificationType.INFO.value,
        verbose_name='Tipo'
    )
    priority = models.IntegerField(
        choices=[(p.value, p.name.title()) for p in NotificationPriority],
        default=NotificationPriority.NORMAL.value,
        verbose_name='Prioridad'
    )
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value.title()) for s in NotificationStatus],
        default=NotificationStatus.PENDING.value,
        verbose_name='Estado'
    )
    data = models.JSONField(default=dict, blank=True, verbose_name='Datos adicionales')
    is_read = models.BooleanField(default=False, verbose_name='Leído')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Leído en')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Expira en')
    
    # Campos de auditoría
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notifications',
        verbose_name='Creado por'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_read']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Marcar como leída."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.status = NotificationStatus.READ.value
            self.save(update_fields=['is_read', 'read_at', 'status'])
    
    def is_expired(self):
        """Verificar si está expirada."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class NotificationChannelModel(models.Model):
    """Modelo de canal de notificación."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_channels',
        verbose_name='Usuario'
    )
    channel_type = models.CharField(
        max_length=20,
        choices=[(c.value, c.value.title()) for c in NotificationChannel],
        verbose_name='Tipo de canal'
    )
    channel_identifier = models.CharField(
        max_length=255,
        verbose_name='Identificador del canal'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_verified = models.BooleanField(default=False, verbose_name='Verificado')
    settings = models.JSONField(default=dict, blank=True, verbose_name='Configuraciones')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='Último uso')
    
    class Meta:
        db_table = 'notification_channels'
        verbose_name = 'Canal de notificación'
        verbose_name_plural = 'Canales de notificación'
        unique_together = ['user', 'channel_type', 'channel_identifier']
        indexes = [
            models.Index(fields=['user', 'channel_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.channel_type} - {self.channel_identifier}"


class NotificationTemplateModel(models.Model):
    """Modelo de plantilla de notificación."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    notification_type = models.CharField(
        max_length=20,
        choices=[(t.value, t.value.title()) for t in NotificationType],
        verbose_name='Tipo'
    )
    title_template = models.CharField(max_length=255, verbose_name='Plantilla de título')
    message_template = models.TextField(verbose_name='Plantilla de mensaje')
    default_priority = models.IntegerField(
        choices=[(p.value, p.name.title()) for p in NotificationPriority],
        default=NotificationPriority.NORMAL.value,
        verbose_name='Prioridad por defecto'
    )
    default_channels = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Canales por defecto'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Creado por'
    )
    
    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'Plantilla de notificación'
        verbose_name_plural = 'Plantillas de notificación'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class NotificationDeliveryModel(models.Model):
    """Modelo de entrega de notificación."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        NotificationModel,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='Notificación'
    )
    channel = models.ForeignKey(
        NotificationChannelModel,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='Canal'
    )
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value.title()) for s in NotificationStatus],
        default=NotificationStatus.PENDING.value,
        verbose_name='Estado'
    )
    delivery_data = models.JSONField(default=dict, blank=True, verbose_name='Datos de entrega')
    error_message = models.TextField(blank=True, verbose_name='Mensaje de error')
    attempts = models.PositiveIntegerField(default=0, verbose_name='Intentos')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado en')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Entregado en')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    
    class Meta:
        db_table = 'notification_deliveries'
        verbose_name = 'Entrega de notificación'
        verbose_name_plural = 'Entregas de notificación'
        unique_together = ['notification', 'channel']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['delivered_at']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} -> {self.channel.channel_type}"
