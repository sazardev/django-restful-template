"""
Auction Application Services.
Servicios de aplicación para subastas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.auctions.domain.entities import AuctionStatus, BidStatus
from apps.auctions.infrastructure.models import Auction, Bid
from apps.auctions.infrastructure.repository import AuctionRepository, BidRepository
from apps.auctions.application.dtos import (
    CreateAuctionDTO, UpdateAuctionDTO, CreateBidDTO,
    AuctionDetailDTO, BidDetailDTO, AuctionSummaryDTO, BidHistoryDTO
)
from apps.vehicles.infrastructure.models import Vehicle
from apps.users.infrastructure.models import User
from shared.domain.exceptions import ValidationError as DomainValidationError
from shared.infrastructure.events import EventBus


class AuctionApplicationService:
    """Servicio de aplicación para subastas."""
    
    def __init__(self):
        self.auction_repository = AuctionRepository()
        self.bid_repository = BidRepository()
        self.event_bus = EventBus()
    
    @transaction.atomic
    def create_auction(self, dto: CreateAuctionDTO, seller_id: UUID) -> AuctionDetailDTO:
        """Crear una nueva subasta."""
        # Validaciones de negocio
        self._validate_auction_creation(dto, seller_id)
        
        # Crear la subasta
        auction = Auction.objects.create(
            vehicle_id=dto.vehicle_id,
            seller_id=seller_id,
            starting_price=dto.starting_price,
            current_price=dto.starting_price,
            reserve_price=dto.reserve_price,
            start_time=dto.start_time,
            end_time=dto.end_time,
            description=dto.description,
            status=AuctionStatus.SCHEDULED.value
        )
        
        # Publicar evento
        self.event_bus.publish('auction_created', {
            'auction_id': str(auction.id),
            'seller_id': str(seller_id),
            'vehicle_id': str(dto.vehicle_id),
            'starting_price': str(dto.starting_price)
        })
        
        return self._auction_to_detail_dto(auction)
    
    def update_auction(self, auction_id: UUID, dto: UpdateAuctionDTO, user_id: UUID) -> AuctionDetailDTO:
        """Actualizar una subasta."""
        auction = self.auction_repository.get_by_id(auction_id)
        
        if not auction:
            raise DomainValidationError("Subasta no encontrada")
        
        if auction.seller_id != user_id:
            raise DomainValidationError("No tienes permisos para modificar esta subasta")
        
        if auction.status != AuctionStatus.SCHEDULED.value:
            raise DomainValidationError("Solo se pueden modificar subastas programadas")
        
        # Actualizar campos
        if dto.description is not None:
            auction.description = dto.description
        if dto.reserve_price is not None:
            auction.reserve_price = dto.reserve_price
        if dto.end_time is not None:
            auction.end_time = dto.end_time
        
        auction.save()
        
        return self._auction_to_detail_dto(auction)
    
    @transaction.atomic
    def place_bid(self, dto: CreateBidDTO, bidder_id: UUID) -> BidDetailDTO:
        """Realizar una puja."""
        auction = self.auction_repository.get_by_id(dto.auction_id)
        
        if not auction:
            raise DomainValidationError("Subasta no encontrada")
        
        # Validaciones de negocio
        self._validate_bid_placement(auction, dto.amount, bidder_id)
        
        # Crear la puja
        bid = Bid.objects.create(
            auction=auction,
            bidder_id=bidder_id,
            amount=dto.amount,
            status=BidStatus.ACTIVE.value
        )
        
        # Actualizar precio actual de la subasta
        auction.current_price = dto.amount
        auction.save()
        
        # Marcar pujas anteriores como superadas
        previous_bids = Bid.objects.filter(
            auction=auction,
            status=BidStatus.ACTIVE.value
        ).exclude(id=bid.id)
        
        previous_bids.update(status=BidStatus.OUTBID.value)
        
        # Publicar evento
        self.event_bus.publish('bid_placed', {
            'bid_id': str(bid.id),
            'auction_id': str(dto.auction_id),
            'bidder_id': str(bidder_id),
            'amount': str(dto.amount),
            'previous_price': str(auction.current_price)
        })
        
        return self._bid_to_detail_dto(bid)
    
    def get_auction_detail(self, auction_id: UUID) -> Optional[AuctionDetailDTO]:
        """Obtener detalle de una subasta."""
        auction = self.auction_repository.get_by_id(auction_id)
        
        if not auction:
            return None
        
        return self._auction_to_detail_dto(auction)
    
    def list_active_auctions(self, limit: int = 10, offset: int = 0) -> List[AuctionSummaryDTO]:
        """Listar subastas activas."""
        auctions = self.auction_repository.get_active_auctions(limit, offset)
        return [self._auction_to_summary_dto(auction) for auction in auctions]
    
    def get_user_auctions(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[AuctionSummaryDTO]:
        """Obtener subastas de un usuario."""
        auctions = self.auction_repository.get_by_seller(user_id, limit, offset)
        return [self._auction_to_summary_dto(auction) for auction in auctions]
    
    def get_bid_history(self, auction_id: UUID) -> BidHistoryDTO:
        """Obtener historial de pujas de una subasta."""
        bids = self.bid_repository.get_by_auction(auction_id)
        bid_dtos = [self._bid_to_detail_dto(bid) for bid in bids]
        
        return BidHistoryDTO(
            bids=bid_dtos,
            total_count=len(bid_dtos),
            auction_id=auction_id
        )
    
    def end_auction(self, auction_id: UUID) -> AuctionDetailDTO:
        """Finalizar una subasta."""
        auction = self.auction_repository.get_by_id(auction_id)
        
        if not auction:
            raise DomainValidationError("Subasta no encontrada")
        
        if auction.status != AuctionStatus.ACTIVE.value:
            raise DomainValidationError("Solo se pueden finalizar subastas activas")
        
        # Determinar el ganador
        winning_bid = self.bid_repository.get_highest_bid(auction_id)
        
        if winning_bid and auction.reserve_price and winning_bid.amount >= auction.reserve_price:
            auction.status = AuctionStatus.COMPLETED.value
            winning_bid.status = BidStatus.WINNING.value
            winning_bid.save()
            
            # Publicar evento de subasta ganada
            self.event_bus.publish('auction_won', {
                'auction_id': str(auction_id),
                'winner_id': str(winning_bid.bidder_id),
                'winning_amount': str(winning_bid.amount)
            })
        else:
            auction.status = AuctionStatus.FAILED.value
            
            # Publicar evento de subasta fallida
            self.event_bus.publish('auction_failed', {
                'auction_id': str(auction_id),
                'final_price': str(auction.current_price)
            })
        
        auction.save()
        
        return self._auction_to_detail_dto(auction)
    
    def _validate_auction_creation(self, dto: CreateAuctionDTO, seller_id: UUID):
        """Validar la creación de una subasta."""
        # Verificar que el vehículo existe y pertenece al vendedor
        try:
            vehicle = Vehicle.objects.get(id=dto.vehicle_id, owner_id=seller_id)
        except Vehicle.DoesNotExist:
            raise DomainValidationError("Vehículo no encontrado o no te pertenece")
        
        # Verificar que no haya subastas activas para este vehículo
        active_auction = Auction.objects.filter(
            vehicle=vehicle,
            status__in=[AuctionStatus.SCHEDULED.value, AuctionStatus.ACTIVE.value]
        ).exists()
        
        if active_auction:
            raise DomainValidationError("Ya existe una subasta activa para este vehículo")
        
        # Validar fechas
        if dto.start_time <= timezone.now():
            raise DomainValidationError("La fecha de inicio debe ser futura")
        
        if dto.end_time <= dto.start_time:
            raise DomainValidationError("La fecha de fin debe ser posterior a la de inicio")
        
        # Validar precios
        if dto.starting_price <= 0:
            raise DomainValidationError("El precio inicial debe ser mayor a 0")
        
        if dto.reserve_price and dto.reserve_price < dto.starting_price:
            raise DomainValidationError("El precio de reserva debe ser mayor o igual al precio inicial")
    
    def _validate_bid_placement(self, auction: Auction, amount: Decimal, bidder_id: UUID):
        """Validar la colocación de una puja."""
        # Verificar que la subasta esté activa
        if auction.status != AuctionStatus.ACTIVE.value:
            raise DomainValidationError("La subasta no está activa")
        
        # Verificar que no haya terminado
        if auction.end_time <= timezone.now():
            raise DomainValidationError("La subasta ha terminado")
        
        # Verificar que el usuario no sea el vendedor
        if auction.seller_id == bidder_id:
            raise DomainValidationError("No puedes pujar en tu propia subasta")
        
        # Verificar que la cantidad sea mayor al precio actual
        if amount <= auction.current_price:
            raise DomainValidationError(f"La puja debe ser mayor a {auction.current_price}")
        
        # Verificar incremento mínimo (por ejemplo, 1% del precio actual)
        min_increment = auction.current_price * Decimal('0.01')
        if amount < auction.current_price + min_increment:
            raise DomainValidationError(f"El incremento mínimo es {min_increment}")
    
    def _auction_to_detail_dto(self, auction: Auction) -> AuctionDetailDTO:
        """Convertir modelo de subasta a DTO detallado."""
        bid_count = Bid.objects.filter(auction=auction).count()
        highest_bid = self.bid_repository.get_highest_bid(auction.id)
        
        return AuctionDetailDTO(
            id=auction.id,
            vehicle_id=auction.vehicle.id,
            vehicle_make=auction.vehicle.make,
            vehicle_model=auction.vehicle.model,
            vehicle_year=auction.vehicle.year,
            seller_id=auction.seller.id,
            seller_name=auction.seller.get_full_name(),
            starting_price=auction.starting_price,
            current_price=auction.current_price,
            reserve_price=auction.reserve_price,
            start_time=auction.start_time,
            end_time=auction.end_time,
            status=auction.status,
            description=auction.description,
            bid_count=bid_count,
            highest_bidder_id=highest_bid.bidder_id if highest_bid else None,
            created_at=auction.created_at
        )
    
    def _auction_to_summary_dto(self, auction: Auction) -> AuctionSummaryDTO:
        """Convertir modelo de subasta a DTO resumido."""
        bid_count = Bid.objects.filter(auction=auction).count()
        
        return AuctionSummaryDTO(
            id=auction.id,
            vehicle_make=auction.vehicle.make,
            vehicle_model=auction.vehicle.model,
            vehicle_year=auction.vehicle.year,
            current_price=auction.current_price,
            end_time=auction.end_time,
            status=auction.status,
            bid_count=bid_count,
            image_url=auction.vehicle.images.first().image.url if auction.vehicle.images.exists() else None
        )
    
    def _bid_to_detail_dto(self, bid: Bid) -> BidDetailDTO:
        """Convertir modelo de puja a DTO detallado."""
        return BidDetailDTO(
            id=bid.id,
            auction_id=bid.auction.id,
            bidder_id=bid.bidder.id,
            bidder_name=bid.bidder.get_full_name(),
            amount=bid.amount,
            status=bid.status,
            created_at=bid.created_at
        )
