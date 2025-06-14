"""
Auction Model Tests.
Tests para los modelos de subastas.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.users.infrastructure.models import User
from apps.vehicles.infrastructure.models import Vehicle, VehicleType
from apps.auctions.infrastructure.models import Auction, Bid
from apps.auctions.domain.entities import AuctionStatus, BidStatus


class AuctionModelTest(TestCase):
    """Tests para el modelo Auction."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        # Crear usuarios
        self.seller = User.objects.create_user(
            email='seller@test.com',
            password='testpass123',
            first_name='John',
            last_name='Seller'
        )
        
        self.bidder = User.objects.create_user(
            email='bidder@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Bidder'
        )
        
        # Crear tipo de vehículo
        self.vehicle_type = VehicleType.objects.create(
            name='Sedan',
            description='Vehículo sedán'
        )
        
        # Crear vehículo
        self.vehicle = Vehicle.objects.create(
            owner=self.seller,
            type=self.vehicle_type,
            make='Toyota',
            model='Corolla',
            year=2020,
            vin='1234567890',
            license_plate='ABC123',
            mileage=50000,
            condition='excellent'
        )
        
        # Fechas para subastas
        self.start_time = timezone.now() + timedelta(hours=1)
        self.end_time = timezone.now() + timedelta(days=7)
    
    def test_create_auction(self):
        """Test crear subasta."""
        auction = Auction.objects.create(
            vehicle=self.vehicle,
            seller=self.seller,
            starting_price=Decimal('10000.00'),
            current_price=Decimal('10000.00'),
            reserve_price=Decimal('15000.00'),
            start_time=self.start_time,
            end_time=self.end_time,
            description='Test auction',
            status=AuctionStatus.SCHEDULED.value
        )
        
        self.assertEqual(auction.vehicle, self.vehicle)
        self.assertEqual(auction.seller, self.seller)
        self.assertEqual(auction.starting_price, Decimal('10000.00'))
        self.assertEqual(auction.current_price, Decimal('10000.00'))
        self.assertEqual(auction.status, AuctionStatus.SCHEDULED.value)
    
    def test_auction_str_representation(self):
        """Test representación string de subasta."""
        auction = Auction.objects.create(
            vehicle=self.vehicle,
            seller=self.seller,
            starting_price=Decimal('10000.00'),
            current_price=Decimal('10000.00'),
            start_time=self.start_time,
            end_time=self.end_time,
            status=AuctionStatus.SCHEDULED.value
        )
        
        expected = f"Subasta: {self.vehicle.make} {self.vehicle.model} - ${auction.current_price}"
        self.assertEqual(str(auction), expected)
    
    def test_auction_ordering(self):
        """Test ordenamiento de subastas."""
        # Crear múltiples subastas
        auction1 = Auction.objects.create(
            vehicle=self.vehicle,
            seller=self.seller,
            starting_price=Decimal('10000.00'),
            current_price=Decimal('10000.00'),
            start_time=self.start_time,
            end_time=self.end_time,
            status=AuctionStatus.SCHEDULED.value
        )
        
        # Crear otro vehículo para segunda subasta
        vehicle2 = Vehicle.objects.create(
            owner=self.seller,
            type=self.vehicle_type,
            make='Honda',
            model='Civic',
            year=2021,
            vin='0987654321',
            license_plate='XYZ789',
            mileage=30000,
            condition='good'
        )
        
        auction2 = Auction.objects.create(
            vehicle=vehicle2,
            seller=self.seller,
            starting_price=Decimal('12000.00'),
            current_price=Decimal('12000.00'),
            start_time=self.start_time + timedelta(hours=1),
            end_time=self.end_time + timedelta(hours=1),
            status=AuctionStatus.SCHEDULED.value
        )
        
        # Verificar ordenamiento (más reciente primero)
        auctions = list(Auction.objects.all())
        self.assertEqual(auctions[0], auction2)
        self.assertEqual(auctions[1], auction1)


class BidModelTest(TestCase):
    """Tests para el modelo Bid."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        # Crear usuarios
        self.seller = User.objects.create_user(
            email='seller@test.com',
            password='testpass123',
            first_name='John',
            last_name='Seller'
        )
        
        self.bidder = User.objects.create_user(
            email='bidder@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Bidder'
        )
        
        # Crear tipo de vehículo
        self.vehicle_type = VehicleType.objects.create(
            name='Sedan',
            description='Vehículo sedán'
        )
        
        # Crear vehículo
        self.vehicle = Vehicle.objects.create(
            owner=self.seller,
            type=self.vehicle_type,
            make='Toyota',
            model='Corolla',
            year=2020,
            vin='1234567890',
            license_plate='ABC123',
            mileage=50000,
            condition='excellent'
        )
        
        # Crear subasta
        self.auction = Auction.objects.create(
            vehicle=self.vehicle,
            seller=self.seller,
            starting_price=Decimal('10000.00'),
            current_price=Decimal('10000.00'),
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(days=6),
            status=AuctionStatus.ACTIVE.value
        )
    
    def test_create_bid(self):
        """Test crear puja."""
        bid = Bid.objects.create(
            auction=self.auction,
            bidder=self.bidder,
            amount=Decimal('11000.00'),
            status=BidStatus.ACTIVE.value
        )
        
        self.assertEqual(bid.auction, self.auction)
        self.assertEqual(bid.bidder, self.bidder)
        self.assertEqual(bid.amount, Decimal('11000.00'))
        self.assertEqual(bid.status, BidStatus.ACTIVE.value)
    
    def test_bid_str_representation(self):
        """Test representación string de puja."""
        bid = Bid.objects.create(
            auction=self.auction,
            bidder=self.bidder,
            amount=Decimal('11000.00'),
            status=BidStatus.ACTIVE.value
        )
        
        expected = f"Puja de {self.bidder.get_full_name()}: ${bid.amount}"
        self.assertEqual(str(bid), expected)
    
    def test_bid_ordering(self):
        """Test ordenamiento de pujas."""
        # Crear múltiples pujas
        bid1 = Bid.objects.create(
            auction=self.auction,
            bidder=self.bidder,
            amount=Decimal('11000.00'),
            status=BidStatus.ACTIVE.value
        )
        
        # Crear otro pujador
        bidder2 = User.objects.create_user(
            email='bidder2@test.com',
            password='testpass123',
            first_name='Bob',
            last_name='Bidder2'
        )
        
        bid2 = Bid.objects.create(
            auction=self.auction,
            bidder=bidder2,
            amount=Decimal('12000.00'),
            status=BidStatus.ACTIVE.value
        )
        
        # Verificar ordenamiento (más reciente primero)
        bids = list(Bid.objects.all())
        self.assertEqual(bids[0], bid2)
        self.assertEqual(bids[1], bid1)
