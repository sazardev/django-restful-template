"""
Base Models for Infrastructure.
Modelos base para la infraestructura.
"""

from django.db import models
import uuid


class BaseModel(models.Model):
    """Modelo base con campos comunes."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Eliminación suave."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        """Restaurar elemento eliminado suavemente."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class AuditableModel(BaseModel):
    """Modelo auditable con información de quién creó/modificó."""
    
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name="Actualizado por"
    )

    class Meta:
        abstract = True
