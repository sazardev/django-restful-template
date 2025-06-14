"""
Auction DTOs (Data Transfer Objects).
Objetos de transferencia de datos para subastas.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID


@dataclass
class CreateAuctionDTO:
    """DTO para crear una subasta."""
    vehicle_id: UUID
    starting_price: Decimal
    reserve_price: Optional[Decimal]
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None


@dataclass
class UpdateAuctionDTO:
    """DTO para actualizar una subasta."""
    description: Optional[str] = None
    reserve_price: Optional[Decimal] = None
    end_time: Optional[datetime] = None


@dataclass
class CreateBidDTO:
    """DTO para crear una puja."""
    auction_id: UUID
    amount: Decimal


@dataclass
class AuctionDetailDTO:
    """DTO detallado de subasta."""
    id: UUID
    vehicle_id: UUID
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    seller_id: UUID
    seller_name: str
    starting_price: Decimal
    current_price: Decimal
    start_time: datetime
    end_time: datetime
    status: str
    bid_count: int
    created_at: datetime
    reserve_price: Optional[Decimal] = None
    description: Optional[str] = None
    highest_bidder_id: Optional[UUID] = None


@dataclass
class BidDetailDTO:
    """DTO detallado de puja."""
    id: UUID
    auction_id: UUID
    bidder_id: UUID
    bidder_name: str
    amount: Decimal
    status: str
    created_at: datetime


@dataclass
class AuctionSummaryDTO:
    """DTO resumido de subasta para listados."""
    id: UUID
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    current_price: Decimal
    end_time: datetime
    status: str
    bid_count: int
    image_url: Optional[str] = None


@dataclass
class BidHistoryDTO:
    """DTO para historial de pujas."""
    bids: List[BidDetailDTO]
    total_count: int
    auction_id: UUID


# Aliases para backward compatibility
AuctionCreateDTO = CreateAuctionDTO
AuctionUpdateDTO = UpdateAuctionDTO
BidCreateDTO = CreateBidDTO
