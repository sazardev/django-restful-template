"""
Auction Domain Entities.
Entidades de dominio para el sistema de subastas.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid


class AuctionStatus(Enum):
    """Estados de subasta."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BidStatus(Enum):
    """Estados de puja."""
    PLACED = "placed"
    WINNING = "winning"
    OUTBID = "outbid"
    CANCELLED = "cancelled"


@dataclass
class Bid:
    """Entidad de puja."""
    id: uuid.UUID
    auction_id: uuid.UUID
    bidder_id: uuid.UUID
    amount: Decimal
    timestamp: datetime
    status: BidStatus
    is_auto_bid: bool = False
    max_amount: Optional[Decimal] = None


@dataclass
class Auction:
    """Entidad principal de subasta."""
    id: uuid.UUID
    vehicle_id: uuid.UUID
    seller_id: uuid.UUID
    title: str
    description: str
    starting_bid: Decimal
    bid_increment: Decimal
    start_time: datetime
    end_time: datetime
    status: AuctionStatus
    created_at: datetime
    updated_at: datetime
    reserve_price: Optional[Decimal] = None
    current_bid: Optional[Decimal] = None
    winner_id: Optional[uuid.UUID] = None
    
    # Datos de pujas
    bids: List[Bid] = None
    total_bids: int = 0
    watchers_count: int = 0
    
    def __post_init__(self):
        """Initialize default values."""
        if self.bids is None:
            self.bids = []
    
    def is_active(self) -> bool:
        """Verifica si la subasta está activa."""
        now = datetime.now()
        return (
            self.status == AuctionStatus.ACTIVE and
            self.start_time <= now <= self.end_time
        )
    
    def can_place_bid(self, amount: Decimal) -> bool:
        """Verifica si se puede realizar una puja."""
        if not self.is_active():
            return False
        
        min_bid = self.current_bid or self.starting_bid
        return amount >= min_bid + self.bid_increment
    
    def get_highest_bid(self) -> Optional[Bid]:
        """Obtiene la puja más alta."""
        if not self.bids:
            return None
        return max(self.bids, key=lambda bid: bid.amount)


@dataclass
class AuctionWatcher:
    """Entidad para usuarios que siguen una subasta."""
    id: uuid.UUID
    auction_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    notify_on_bid: bool = True
    notify_on_ending: bool = True
