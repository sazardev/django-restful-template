"""
Auction Serializers.
Serializadores para subastas.
"""

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal

from apps.auctions.infrastructure.models import Auction, Bid
from apps.vehicles.presentation.serializers import VehicleSummarySerializer


class AuctionCreateSerializer(serializers.Serializer):
    """Serializer para crear subasta."""
    
    vehicle_id = serializers.UUIDField()
    starting_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    reserve_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'), required=False, allow_null=True)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_start_time(self, value):
        """Validar fecha de inicio."""
        if value <= timezone.now():
            raise serializers.ValidationError("La fecha de inicio debe ser futura")
        return value
    
    def validate(self, data):
        """Validaciones cruzadas."""
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("La fecha de fin debe ser posterior a la de inicio")
        
        if data.get('reserve_price') and data['reserve_price'] < data['starting_price']:
            raise serializers.ValidationError("El precio de reserva debe ser mayor o igual al precio inicial")
        
        return data


class AuctionUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar subasta."""
    
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    reserve_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'), required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False)


class BidCreateSerializer(serializers.Serializer):
    """Serializer para crear puja."""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    
    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        super().__init__(*args, **kwargs)
    
    def validate_amount(self, value):
        """Validar cantidad de la puja."""
        if self.auction and value <= self.auction.current_price:
            raise serializers.ValidationError(f"La puja debe ser mayor a {self.auction.current_price}")
        
        return value


class BidDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para puja."""
    
    bidder_name = serializers.CharField(source='bidder.get_full_name', read_only=True)
    bidder_email = serializers.CharField(source='bidder.email', read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'amount', 'status', 'created_at',
            'bidder_name', 'bidder_email'
        ]
        read_only_fields = fields


class BidSummarySerializer(serializers.ModelSerializer):
    """Serializer resumido para puja."""
    
    bidder_name = serializers.CharField(source='bidder.get_full_name', read_only=True)
    
    class Meta:
        model = Bid
        fields = ['id', 'amount', 'created_at', 'bidder_name']
        read_only_fields = fields


class AuctionDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para subasta."""
    
    vehicle = VehicleSummarySerializer(read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    seller_email = serializers.CharField(source='seller.email', read_only=True)
    bid_count = serializers.SerializerMethodField()
    highest_bid = serializers.SerializerMethodField()
    user_highest_bid = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Auction
        fields = [
            'id', 'vehicle', 'seller_name', 'seller_email',
            'starting_price', 'current_price', 'reserve_price',
            'start_time', 'end_time', 'status', 'description',
            'bid_count', 'highest_bid', 'user_highest_bid',
            'time_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_bid_count(self, obj):
        """Obtener número de pujas."""
        return obj.bids.count()
    
    def get_highest_bid(self, obj):
        """Obtener puja más alta."""
        highest_bid = obj.bids.order_by('-amount').first()
        if highest_bid:
            return BidSummarySerializer(highest_bid).data
        return None
    
    def get_user_highest_bid(self, obj):
        """Obtener puja más alta del usuario actual."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_bid = obj.bids.filter(bidder=request.user).order_by('-amount').first()
            if user_bid:
                return BidSummarySerializer(user_bid).data
        return None
    
    def get_time_remaining(self, obj):
        """Obtener tiempo restante."""
        if obj.end_time > timezone.now():
            remaining = obj.end_time - timezone.now()
            return {
                'days': remaining.days,
                'hours': remaining.seconds // 3600,
                'minutes': (remaining.seconds % 3600) // 60,
                'total_seconds': remaining.total_seconds()
            }
        return None


class AuctionSummarySerializer(serializers.ModelSerializer):
    """Serializer resumido para subasta."""
    
    vehicle_info = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Auction
        fields = [
            'id', 'vehicle_info', 'current_price', 'end_time',
            'status', 'bid_count', 'time_remaining', 'image_url'
        ]
        read_only_fields = fields
    
    def get_vehicle_info(self, obj):
        """Obtener información resumida del vehículo."""
        return {
            'id': obj.vehicle.id,
            'make': obj.vehicle.make,
            'model': obj.vehicle.model,
            'year': obj.vehicle.year,
        }
    
    def get_bid_count(self, obj):
        """Obtener número de pujas."""
        return obj.bids.count()
    
    def get_time_remaining(self, obj):
        """Obtener tiempo restante."""
        if obj.end_time > timezone.now():
            remaining = obj.end_time - timezone.now()
            return remaining.total_seconds()
        return 0
    
    def get_image_url(self, obj):
        """Obtener URL de imagen del vehículo."""
        first_image = obj.vehicle.images.first()
        if first_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None


class AuctionListSerializer(serializers.ModelSerializer):
    """Serializer para listado de subastas."""
    
    vehicle_make = serializers.CharField(source='vehicle.make', read_only=True)
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)
    vehicle_year = serializers.CharField(source='vehicle.year', read_only=True)
    bid_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Auction
        fields = [
            'id', 'vehicle_make', 'vehicle_model', 'vehicle_year',
            'current_price', 'end_time', 'status', 'bid_count'
        ]
        read_only_fields = fields
    
    def get_bid_count(self, obj):
        """Obtener número de pujas."""
        return obj.bids.count()


# Aliases para backward compatibility
CreateAuctionSerializer = AuctionCreateSerializer
UpdateAuctionSerializer = AuctionUpdateSerializer
CreateBidSerializer = BidCreateSerializer
