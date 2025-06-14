"""
Auction Domain Entities.
Entidades de dominio para el sistema de subastas.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict
from uuid import UUID


class AuctionStatus(Enum):
    """Estados de subasta."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BidStatus(Enum):
    """Estados de oferta."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    OUTBID = "outbid"


class AuctionType(Enum):
    """Tipos de subasta."""
    FORWARD = "forward"  # Subasta normal (precio sube)
    REVERSE = "reverse"  # Subasta inversa (precio baja)
    SEALED = "sealed"    # Subasta sellada
    DUTCH = "dutch"      # Subasta holandesa


@dataclass
class BidEntity:
    """Entidad de oferta."""
    id: UUID
    auction_id: UUID
    bidder_id: UUID
    amount: Decimal
    submitted_at: datetime
    status: BidStatus
    is_automatic: bool = False
    notes: Optional[str] = None
    
    def is_valid_for_auction(self, auction: 'AuctionEntity') -> bool:
        """Verificar si la oferta es válida para la subasta."""
        if auction.status != AuctionStatus.ACTIVE:
            return False
        
        if auction.auction_type == AuctionType.FORWARD:
            return self.amount > auction.current_highest_bid
        elif auction.auction_type == AuctionType.REVERSE:
            return self.amount < auction.current_lowest_bid
        
        return True


@dataclass
class AuctionRequirements:
    """Requisitos de la subasta - Value Object."""
    min_vehicle_capacity_kg: Optional[Decimal] = None
    min_vehicle_capacity_m3: Optional[Decimal] = None
    required_vehicle_types: List[str] = None
    required_certifications: List[str] = None
    max_delivery_days: Optional[int] = None
    insurance_coverage_required: bool = False
    
    def __post_init__(self):
        if self.required_vehicle_types is None:
            self.required_vehicle_types = []
        if self.required_certifications is None:
            self.required_certifications = []


@dataclass
class ShipmentDetails:
    """Detalles del envío - Value Object."""
    origin_address: str
    destination_address: str
    pickup_date: datetime
    delivery_date: datetime
    weight_kg: Decimal
    volume_m3: Decimal
    cargo_description: str
    special_instructions: Optional[str] = None
    fragile: bool = False
    temperature_controlled: bool = False
    
    def __post_init__(self):
        if self.weight_kg <= 0:
            raise ValueError("El peso debe ser mayor a 0")
        if self.volume_m3 <= 0:
            raise ValueError("El volumen debe ser mayor a 0")
        if self.pickup_date >= self.delivery_date:
            raise ValueError("La fecha de entrega debe ser posterior a la de recogida")


@dataclass
class AuctionEntity:
    """Entidad principal de subasta."""
    id: UUID
    title: str
    description: str
    creator_id: UUID
    auction_type: AuctionType
    status: AuctionStatus
    shipment_details: ShipmentDetails
    requirements: AuctionRequirements
    starting_price: Decimal
    reserve_price: Optional[Decimal]
    current_highest_bid: Decimal
    current_lowest_bid: Decimal
    winner_bid_id: Optional[UUID]
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime
    bids: List[BidEntity] = None
    auto_extend_minutes: int = 5
    bid_increment: Decimal = Decimal('10.00')
    
    def __post_init__(self):
        if self.bids is None:
            self.bids = []
        
        # Inicializar precios según tipo de subasta
        if self.auction_type == AuctionType.FORWARD:
            self.current_highest_bid = self.starting_price
        elif self.auction_type == AuctionType.REVERSE:
            self.current_lowest_bid = self.starting_price
    
    def can_place_bid(self, bidder_id: UUID) -> bool:
        """Verificar si se puede hacer una oferta."""
        if self.status != AuctionStatus.ACTIVE:
            return False
        
        if self.creator_id == bidder_id:
            return False
        
        now = datetime.now()
        if now < self.start_time or now > self.end_time:
            return False
        
        return True
    
    def place_bid(self, bid: BidEntity) -> bool:
        """Colocar una oferta."""
        if not self.can_place_bid(bid.bidder_id):
            return False
        
        if not bid.is_valid_for_auction(self):
            return False
        
        # Marcar ofertas anteriores como superadas
        for existing_bid in self.bids:
            if existing_bid.status == BidStatus.PENDING:
                existing_bid.status = BidStatus.OUTBID
        
        # Aceptar nueva oferta
        bid.status = BidStatus.ACCEPTED
        self.bids.append(bid)
        
        # Actualizar precio actual
        if self.auction_type == AuctionType.FORWARD:
            self.current_highest_bid = bid.amount
        elif self.auction_type == AuctionType.REVERSE:
            self.current_lowest_bid = bid.amount
        
        # Auto-extensión si la oferta llega cerca del final
        time_left = self.end_time - datetime.now()
        if time_left.total_seconds() < self.auto_extend_minutes * 60:
            from datetime import timedelta
            self.end_time += timedelta(minutes=self.auto_extend_minutes)
        
        self.updated_at = datetime.now()
        return True
    
    def start_auction(self) -> None:
        """Iniciar la subasta."""
        if self.status != AuctionStatus.PUBLISHED:
            raise ValueError("Solo se pueden iniciar subastas publicadas")
        
        if datetime.now() < self.start_time:
            raise ValueError("No se puede iniciar antes de la hora programada")
        
        self.status = AuctionStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def end_auction(self) -> Optional[UUID]:
        """Finalizar la subasta y determinar ganador."""
        if self.status != AuctionStatus.ACTIVE:
            raise ValueError("Solo se pueden finalizar subastas activas")
        
        winning_bid = self.get_winning_bid()
        if winning_bid:
            self.winner_bid_id = winning_bid.id
        
        self.status = AuctionStatus.COMPLETED
        self.updated_at = datetime.now()
        
        return self.winner_bid_id
    
    def cancel_auction(self) -> None:
        """Cancelar la subasta."""
        if self.status in [AuctionStatus.COMPLETED, AuctionStatus.CANCELLED]:
            raise ValueError("No se puede cancelar una subasta completada o ya cancelada")
        
        self.status = AuctionStatus.CANCELLED
        self.updated_at = datetime.now()
    
    def get_winning_bid(self) -> Optional[BidEntity]:
        """Obtener la oferta ganadora."""
        if not self.bids:
            return None
        
        if self.auction_type == AuctionType.FORWARD:
            return max(
                [bid for bid in self.bids if bid.status == BidStatus.ACCEPTED],
                key=lambda b: b.amount,
                default=None
            )
        elif self.auction_type == AuctionType.REVERSE:
            return min(
                [bid for bid in self.bids if bid.status == BidStatus.ACCEPTED],
                key=lambda b: b.amount,
                default=None
            )
        
        return None
    
    def get_bid_history(self) -> List[BidEntity]:
        """Obtener historial de ofertas ordenado."""
        return sorted(self.bids, key=lambda b: b.submitted_at, reverse=True)
    
    def is_expired(self) -> bool:
        """Verificar si la subasta ha expirado."""
        return datetime.now() > self.end_time
    
    def time_remaining(self) -> Optional[int]:
        """Obtener segundos restantes (None si ha expirado)."""
        if self.is_expired():
            return None
        
        delta = self.end_time - datetime.now()
        return int(delta.total_seconds())
    
    def meets_reserve_price(self) -> bool:
        """Verificar si se alcanzó el precio de reserva."""
        if not self.reserve_price:
            return True
        
        if self.auction_type == AuctionType.FORWARD:
            return self.current_highest_bid >= self.reserve_price
        elif self.auction_type == AuctionType.REVERSE:
            return self.current_lowest_bid <= self.reserve_price
        
        return False
    
    def calculate_next_bid_amount(self) -> Decimal:
        """Calcular el monto mínimo para la próxima oferta."""
        if self.auction_type == AuctionType.FORWARD:
            return self.current_highest_bid + self.bid_increment
        elif self.auction_type == AuctionType.REVERSE:
            return max(
                Decimal('0.01'), 
                self.current_lowest_bid - self.bid_increment
            )
        
        return self.starting_price
