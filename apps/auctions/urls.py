"""
Auction URLs.
URLs para la aplicación de subastas.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.auctions.presentation.views import AuctionViewSet, BidViewSet

app_name = 'auctions'

# Router para ViewSets
router = DefaultRouter()
router.register(r'auctions', AuctionViewSet)
router.register(r'bids', BidViewSet)

urlpatterns = [
    # API endpoints
    path('api/v1/', include(router.urls)),
]
