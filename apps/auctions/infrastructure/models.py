"""
Auction Django Models.
Modelos de Django para el sistema de subastas.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.auctions.domain.entities import AuctionStatus, BidStatus


class Auction(models.Model):
    """Modelo de subasta."""
    
    class Meta:
        verbose_name = _('Subasta')
        verbose_name_plural = _('Subastas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['end_time']),
        ]
    
    # Campos únicos
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Relaciones
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='auctions',
        verbose_name=_('Vehículo')
    )
    
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auctions_as_seller',
        verbose_name=_('Vendedor')
    )
    
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='auctions_won',
        null=True,
        blank=True,
        verbose_name=_('Ganador')
    )
    
    # Información básica
    title = models.CharField(
        max_length=200,
        verbose_name=_('Título')
    )
    
    description = models.TextField(
        verbose_name=_('Descripción')
    )
    
    # Precios y pujas
    starting_bid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Puja inicial')
    )
    
    reserve_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_('Precio de reserva'),
        help_text=_('Precio mínimo para vender')
    )
    
    current_bid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_('Puja actual')
    )
    
    bid_increment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Incremento de puja')
    )
    
    # Fechas
    start_time = models.DateTimeField(
        verbose_name=_('Fecha de inicio')
    )
    
    end_time = models.DateTimeField(
        verbose_name=_('Fecha de fin')
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value.title()) for status in AuctionStatus],
        default=AuctionStatus.DRAFT.value,
        verbose_name=_('Estado')
    )
    
    # Estadísticas
    total_bids = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total de pujas')
    )
    
    watchers_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Seguidores')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creado en')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Actualizado en')
    )
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def is_active(self):
        """Verifica si la subasta está activa."""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == AuctionStatus.ACTIVE.value and
            self.start_time <= now <= self.end_time
        )


class Bid(models.Model):
    """Modelo de puja."""
    
    class Meta:
        verbose_name = _('Puja')
        verbose_name_plural = _('Pujas')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['auction', 'amount']),
            models.Index(fields=['bidder', 'timestamp']),
            models.Index(fields=['status']),
        ]
        unique_together = ['auction', 'bidder', 'timestamp']
    
    # Campos únicos
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Relaciones
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name=_('Subasta')
    )
    
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name=_('Pujador')
    )
    
    # Información de la puja
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Cantidad')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha y hora')
    )
    
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value.title()) for status in BidStatus],
        default=BidStatus.PLACED.value,
        verbose_name=_('Estado')
    )
    
    # Puja automática
    is_auto_bid = models.BooleanField(
        default=False,
        verbose_name=_('Es puja automática')
    )
    
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_('Cantidad máxima'),
        help_text=_('Para pujas automáticas')
    )
    
    def __str__(self):
        return f"{self.bidder.username} - ${self.amount} en {self.auction.title}"


class AuctionWatcher(models.Model):
    """Modelo para usuarios que siguen una subasta."""
    
    class Meta:
        verbose_name = _('Seguidor de subasta')
        verbose_name_plural = _('Seguidores de subasta')
        unique_together = ['auction', 'user']
        indexes = [
            models.Index(fields=['auction', 'user']),
        ]
    
    # Campos únicos
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Relaciones
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='watchers',
        verbose_name=_('Subasta')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watched_auctions',
        verbose_name=_('Usuario')
    )
    
    # Configuraciones de notificación
    notify_on_bid = models.BooleanField(
        default=True,
        verbose_name=_('Notificar en nueva puja')
    )
    
    notify_on_ending = models.BooleanField(
        default=True,
        verbose_name=_('Notificar al finalizar')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creado en')
    )
    
    def __str__(self):
        return f"{self.user.username} siguiendo {self.auction.title}"
