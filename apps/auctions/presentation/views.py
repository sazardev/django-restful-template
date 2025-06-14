"""
Auction Views.
Vistas para subastas usando Clean Architecture.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.auctions.infrastructure.models import Auction, Bid
from apps.auctions.application.services import AuctionApplicationService
from apps.auctions.application.dtos import CreateAuctionDTO, UpdateAuctionDTO, CreateBidDTO
from apps.auctions.presentation.serializers import (
    AuctionCreateSerializer, AuctionUpdateSerializer, AuctionDetailSerializer,
    AuctionSummarySerializer, BidCreateSerializer, BidDetailSerializer
)
from shared.infrastructure.permissions import IsOwnerOrReadOnlyPermission
from shared.infrastructure.pagination import StandardPagination
from shared.domain.exceptions import ValidationError as DomainValidationError


class AuctionViewSet(ModelViewSet):
    """ViewSet para subastas."""
    
    queryset = Auction.objects.select_related('vehicle', 'seller').prefetch_related('bids')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'vehicle__make', 'vehicle__model']
    search_fields = ['vehicle__make', 'vehicle__model', 'description']
    ordering_fields = ['created_at', 'end_time', 'current_price']
    ordering = ['-created_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auction_service = AuctionApplicationService()
    
    def get_serializer_class(self):
        """Obtener la clase de serializer según la acción."""
        if self.action == 'create':
            return AuctionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AuctionUpdateSerializer
        elif self.action == 'retrieve':
            return AuctionDetailSerializer
        elif self.action == 'place_bid':
            return BidCreateSerializer
        else:
            return AuctionSummarySerializer
    
    def get_permissions(self):
        """Obtener permisos según la acción."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnlyPermission()]
        return [IsAuthenticated()]
    
    def create(self, request):
        """Crear nueva subasta."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Crear DTO desde los datos validados
            dto = CreateAuctionDTO(**serializer.validated_data)
            
            # Usar el servicio de aplicación
            auction_detail = self.auction_service.create_auction(dto, request.user.id)
            
            # Obtener la subasta creada para serializar
            auction = Auction.objects.get(id=auction_detail.id)
            response_serializer = AuctionDetailSerializer(auction, context={'request': request})
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except DomainValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, pk=None):
        """Actualizar subasta."""
        auction = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Crear DTO desde los datos validados
            dto = UpdateAuctionDTO(**serializer.validated_data)
            
            # Usar el servicio de aplicación
            auction_detail = self.auction_service.update_auction(auction.id, dto, request.user.id)
            
            # Obtener la subasta actualizada para serializar
            updated_auction = Auction.objects.get(id=auction_detail.id)
            response_serializer = AuctionDetailSerializer(updated_auction, context={'request': request})
            
            return Response(response_serializer.data)
        
        except DomainValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, pk=None):
        """Obtener detalle de subasta."""
        auction = self.get_object()
        serializer = AuctionDetailSerializer(auction, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def place_bid(self, request, pk=None):
        """Realizar una puja."""
        auction = self.get_object()
        serializer = BidCreateSerializer(data=request.data, auction=auction)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Crear DTO para la puja
            dto = CreateBidDTO(
                auction_id=auction.id,
                amount=serializer.validated_data['amount']
            )
            
            # Usar el servicio de aplicación
            bid_detail = self.auction_service.place_bid(dto, request.user.id)
            
            # Obtener la puja creada para serializar
            bid = Bid.objects.get(id=bid_detail.id)
            response_serializer = BidDetailSerializer(bid, context={'request': request})
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except DomainValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def bids(self, request, pk=None):
        """Obtener historial de pujas de una subasta."""
        auction = self.get_object()
        bids = Bid.objects.filter(auction=auction).select_related('bidder').order_by('-created_at')
        
        # Paginación
        page = self.paginate_queryset(bids)
        if page is not None:
            serializer = BidDetailSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BidDetailSerializer(bids, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_auctions(self, request):
        """Obtener subastas del usuario actual."""
        auctions = Auction.objects.filter(seller=request.user).select_related('vehicle').order_by('-created_at')
        
        # Paginación
        page = self.paginate_queryset(auctions)
        if page is not None:
            serializer = AuctionSummarySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = AuctionSummarySerializer(auctions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_bids(self, request):
        """Obtener pujas del usuario actual."""
        bids = Bid.objects.filter(bidder=request.user).select_related('auction', 'auction__vehicle').order_by('-created_at')
        
        # Paginación
        page = self.paginate_queryset(bids)
        if page is not None:
            serializer = BidDetailSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BidDetailSerializer(bids, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Obtener subastas activas."""
        from apps.auctions.domain.entities import AuctionStatus
        
        auctions = Auction.objects.filter(
            status=AuctionStatus.ACTIVE.value
        ).select_related('vehicle', 'seller').order_by('end_time')
        
        # Paginación
        page = self.paginate_queryset(auctions)
        if page is not None:
            serializer = AuctionSummarySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = AuctionSummarySerializer(auctions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def ending_soon(self, request):
        """Obtener subastas que terminan pronto."""
        from apps.auctions.domain.entities import AuctionStatus
        from django.utils import timezone
        from datetime import timedelta
        
        # Subastas que terminan en las próximas 24 horas
        end_time_threshold = timezone.now() + timedelta(hours=24)
        
        auctions = Auction.objects.filter(
            status=AuctionStatus.ACTIVE.value,
            end_time__lte=end_time_threshold
        ).select_related('vehicle', 'seller').order_by('end_time')
        
        # Paginación
        page = self.paginate_queryset(auctions)
        if page is not None:
            serializer = AuctionSummarySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = AuctionSummarySerializer(auctions, many=True, context={'request': request})
        return Response(serializer.data)


class BidViewSet(ModelViewSet):
    """ViewSet para pujas."""
    
    queryset = Bid.objects.select_related('auction', 'bidder')
    serializer_class = BidDetailSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'auction']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrar pujas según el usuario."""
        # Los usuarios solo pueden ver sus propias pujas
        return super().get_queryset().filter(bidder=self.request.user)
    
    def create(self, request):
        """Crear puja (no permitido directamente, usar auction.place_bid)."""
        return Response(
            {'error': 'Use el endpoint /auctions/{id}/place_bid/ para realizar pujas'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, pk=None):
        """Actualizar puja (no permitido)."""
        return Response(
            {'error': 'No se pueden modificar las pujas una vez realizadas'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, pk=None):
        """Eliminar puja (no permitido)."""
        return Response(
            {'error': 'No se pueden eliminar las pujas una vez realizadas'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
