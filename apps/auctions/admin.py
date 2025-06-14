"""
Auction Admin Configuration.
Configuración del admin para subastas.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from apps.auctions.infrastructure.models import Auction, Bid, AuctionWatcher


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    """Configuración del admin para subastas."""
    
    list_display = [
        'title', 'seller', 'status', 'current_bid_display', 
        'total_bids', 'start_time', 'end_time', 'is_active_display'
    ]
    list_filter = ['status', 'start_time', 'end_time', 'created_at']
    search_fields = ['title', 'description', 'seller__username', 'seller__email']
    readonly_fields = ['created_at', 'updated_at', 'total_bids', 'watchers_count']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        (_('Información básica'), {
            'fields': ('title', 'description', 'vehicle', 'seller')
        }),
        (_('Configuración de precios'), {
            'fields': ('starting_bid', 'reserve_price', 'current_bid', 'bid_increment')
        }),
        (_('Fechas'), {
            'fields': ('start_time', 'end_time')
        }),
        (_('Estado y estadísticas'), {
            'fields': ('status', 'winner', 'total_bids', 'watchers_count')
        }),
        (_('Metadatos'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_bid_display(self, obj):
        """Muestra la puja actual formateada."""
        if obj.current_bid:
            return f"${obj.current_bid:,.2f}"
        return "Sin pujas"
    current_bid_display.short_description = "Puja actual"
    
    def is_active_display(self, obj):
        """Muestra si la subasta está activa."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activa</span>')
        return format_html('<span style="color: red;">✗ Inactiva</span>')
    is_active_display.short_description = "Estado"
    
    def get_queryset(self, request):
        """Optimiza las consultas."""
        return super().get_queryset(request).select_related(
            'seller', 'vehicle', 'winner'
        ).prefetch_related('bids')


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """Configuración del admin para pujas."""
    
    list_display = [
        'auction_link', 'bidder', 'amount_display', 'status', 
        'is_auto_bid', 'timestamp'
    ]
    list_filter = ['status', 'is_auto_bid', 'timestamp']
    search_fields = ['auction__title', 'bidder__username', 'bidder__email']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Información de la puja'), {
            'fields': ('auction', 'bidder', 'amount', 'status')
        }),
        (_('Puja automática'), {
            'fields': ('is_auto_bid', 'max_amount')
        }),
        (_('Metadatos'), {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    def auction_link(self, obj):
        """Enlace a la subasta."""
        url = reverse('admin:auctions_auction_change', args=[obj.auction.pk])
        return format_html('<a href="{}">{}</a>', url, obj.auction.title)
    auction_link.short_description = "Subasta"
    
    def amount_display(self, obj):
        """Muestra la cantidad formateada."""
        return f"${obj.amount:,.2f}"
    amount_display.short_description = "Cantidad"
    
    def get_queryset(self, request):
        """Optimiza las consultas."""
        return super().get_queryset(request).select_related(
            'auction', 'bidder'
        )


@admin.register(AuctionWatcher)
class AuctionWatcherAdmin(admin.ModelAdmin):
    """Configuración del admin para seguidores de subastas."""
    
    list_display = [
        'user', 'auction_link', 'notify_on_bid', 'notify_on_ending', 'created_at'
    ]
    list_filter = ['notify_on_bid', 'notify_on_ending', 'created_at']
    search_fields = ['user__username', 'user__email', 'auction__title']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Información del seguidor'), {
            'fields': ('user', 'auction')
        }),
        (_('Preferencias de notificación'), {
            'fields': ('notify_on_bid', 'notify_on_ending')
        }),
        (_('Metadatos'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def auction_link(self, obj):
        """Enlace a la subasta."""
        url = reverse('admin:auctions_auction_change', args=[obj.auction.pk])
        return format_html('<a href="{}">{}</a>', url, obj.auction.title)
    auction_link.short_description = "Subasta"
    
    def get_queryset(self, request):
        """Optimiza las consultas."""
        return super().get_queryset(request).select_related(
            'user', 'auction'
        )