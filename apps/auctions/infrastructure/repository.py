"""
Auction Infrastructure Repository.
Repositorio de infraestructura para subastas.
"""

from typing import List, Optional
from uuid import UUID
from django.db.models import QuerySet

from apps.auctions.infrastructure.models import Auction, Bid
from apps.auctions.domain.entities import AuctionStatus


class AuctionRepository:
    """Repositorio para subastas."""
    
    def get_by_id(self, auction_id: UUID) -> Optional[Auction]:
        """Obtener subasta por ID."""
        try:
            return Auction.objects.select_related('vehicle', 'seller').get(id=auction_id)
        except Auction.DoesNotExist:
            return None
    
    def get_active_auctions(self, limit: int = 10, offset: int = 0) -> QuerySet[Auction]:
        """Obtener subastas activas."""
        return Auction.objects.filter(
            status=AuctionStatus.ACTIVE.value
        ).select_related('vehicle', 'seller').order_by('end_time')[offset:offset + limit]
    
    def get_by_seller(self, seller_id: UUID, limit: int = 10, offset: int = 0) -> QuerySet[Auction]:
        """Obtener subastas por vendedor."""
        return Auction.objects.filter(
            seller_id=seller_id
        ).select_related('vehicle').order_by('-created_at')[offset:offset + limit]
    
    def get_ending_soon(self, hours: int = 24) -> QuerySet[Auction]:
        """Obtener subastas que terminan pronto."""
        from django.utils import timezone
        from datetime import timedelta
        
        end_time_threshold = timezone.now() + timedelta(hours=hours)
        
        return Auction.objects.filter(
            status=AuctionStatus.ACTIVE.value,
            end_time__lte=end_time_threshold
        ).select_related('vehicle', 'seller')
    
    def create(self, **kwargs) -> Auction:
        """Crear nueva subasta."""
        return Auction.objects.create(**kwargs)
    
    def update(self, auction: Auction, **kwargs) -> Auction:
        """Actualizar subasta."""
        for key, value in kwargs.items():
            setattr(auction, key, value)
        auction.save()
        return auction
    
    def delete(self, auction: Auction) -> bool:
        """Eliminar subasta."""
        auction.delete()
        return True


class BidRepository:
    """Repositorio para pujas."""
    
    def get_by_id(self, bid_id: UUID) -> Optional[Bid]:
        """Obtener puja por ID."""
        try:
            return Bid.objects.select_related('auction', 'bidder').get(id=bid_id)
        except Bid.DoesNotExist:
            return None
    
    def get_by_auction(self, auction_id: UUID) -> QuerySet[Bid]:
        """Obtener pujas por subasta."""
        return Bid.objects.filter(
            auction_id=auction_id
        ).select_related('bidder').order_by('-created_at')
    
    def get_by_bidder(self, bidder_id: UUID) -> QuerySet[Bid]:
        """Obtener pujas por pujador."""
        return Bid.objects.filter(
            bidder_id=bidder_id
        ).select_related('auction', 'auction__vehicle').order_by('-created_at')
    
    def get_highest_bid(self, auction_id: UUID) -> Optional[Bid]:
        """Obtener la puja más alta de una subasta."""
        return Bid.objects.filter(
            auction_id=auction_id
        ).select_related('bidder').order_by('-amount').first()
    
    def get_user_highest_bid(self, auction_id: UUID, bidder_id: UUID) -> Optional[Bid]:
        """Obtener la puja más alta de un usuario en una subasta."""
        return Bid.objects.filter(
            auction_id=auction_id,
            bidder_id=bidder_id
        ).order_by('-amount').first()
    
    def create(self, **kwargs) -> Bid:
        """Crear nueva puja."""
        return Bid.objects.create(**kwargs)
    
    def update(self, bid: Bid, **kwargs) -> Bid:
        """Actualizar puja."""
        for key, value in kwargs.items():
            setattr(bid, key, value)
        bid.save()
        return bid
