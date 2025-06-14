"""
Auction Signals.
Señales para el sistema de subastas.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.auctions.infrastructure.models import Auction, Bid
from apps.auctions.domain.entities import AuctionStatus, BidStatus
from shared.infrastructure.events import EventBus


@receiver(pre_save, sender=Auction)
def auction_status_change(sender, instance, **kwargs):
    """Manejar cambios de estado en subastas."""
    if instance.pk:  # Solo para actualizaciones
        try:
            old_instance = Auction.objects.get(pk=instance.pk)
            
            # Detectar activación automática de subasta
            if (old_instance.status == AuctionStatus.SCHEDULED.value and 
                instance.start_time <= timezone.now() and
                instance.status == AuctionStatus.SCHEDULED.value):
                instance.status = AuctionStatus.ACTIVE.value
                
                # Publicar evento de subasta iniciada
                EventBus().publish('auction_started', {
                    'auction_id': str(instance.id),
                    'vehicle_id': str(instance.vehicle_id),
                    'seller_id': str(instance.seller_id),
                    'starting_price': str(instance.starting_price)
                })
            
            # Detectar finalización automática de subasta
            elif (old_instance.status == AuctionStatus.ACTIVE.value and
                  instance.end_time <= timezone.now() and
                  instance.status == AuctionStatus.ACTIVE.value):
                # Determinar el resultado de la subasta
                highest_bid = instance.bids.order_by('-amount').first()
                
                if highest_bid and instance.reserve_price and highest_bid.amount >= instance.reserve_price:
                    instance.status = AuctionStatus.COMPLETED.value
                    highest_bid.status = BidStatus.WINNING.value
                    highest_bid.save()
                    
                    # Publicar evento de subasta completada
                    EventBus().publish('auction_completed', {
                        'auction_id': str(instance.id),
                        'winner_id': str(highest_bid.bidder_id),
                        'winning_amount': str(highest_bid.amount),
                        'vehicle_id': str(instance.vehicle_id)
                    })
                else:
                    instance.status = AuctionStatus.FAILED.value
                    
                    # Publicar evento de subasta fallida
                    EventBus().publish('auction_failed', {
                        'auction_id': str(instance.id),
                        'final_price': str(instance.current_price),
                        'vehicle_id': str(instance.vehicle_id)
                    })
                    
        except Auction.DoesNotExist:
            pass


@receiver(post_save, sender=Auction)
def auction_created(sender, instance, created, **kwargs):
    """Manejar creación de subasta."""
    if created:
        # Publicar evento de subasta creada
        EventBus().publish('auction_created', {
            'auction_id': str(instance.id),
            'seller_id': str(instance.seller_id),
            'vehicle_id': str(instance.vehicle_id),
            'starting_price': str(instance.starting_price),
            'start_time': instance.start_time.isoformat(),
            'end_time': instance.end_time.isoformat()
        })


@receiver(post_save, sender=Bid)
def bid_placed(sender, instance, created, **kwargs):
    """Manejar colocación de puja."""
    if created:
        # Actualizar pujas anteriores como superadas
        previous_bids = Bid.objects.filter(
            auction=instance.auction,
            status=BidStatus.ACTIVE.value
        ).exclude(id=instance.id)
        
        previous_bids.update(status=BidStatus.OUTBID.value)
        
        # Actualizar precio actual de la subasta
        instance.auction.current_price = instance.amount
        instance.auction.save(update_fields=['current_price'])
        
        # Publicar evento de puja realizada
        EventBus().publish('bid_placed', {
            'bid_id': str(instance.id),
            'auction_id': str(instance.auction_id),
            'bidder_id': str(instance.bidder_id),
            'amount': str(instance.amount),
            'new_current_price': str(instance.amount),
            'bidder_name': instance.bidder.get_full_name()
        })
        
        # Notificar al vendedor sobre nueva puja
        EventBus().publish('new_bid_notification', {
            'recipient_id': str(instance.auction.seller_id),
            'auction_id': str(instance.auction_id),
            'bid_amount': str(instance.amount),
            'bidder_name': instance.bidder.get_full_name(),
            'vehicle_info': f"{instance.auction.vehicle.make} {instance.auction.vehicle.model} {instance.auction.vehicle.year}"
        })
        
        # Notificar a otros pujadores que fueron superados
        outbid_users = Bid.objects.filter(
            auction=instance.auction,
            status=BidStatus.OUTBID.value
        ).exclude(bidder=instance.bidder).values_list('bidder_id', flat=True).distinct()
        
        for user_id in outbid_users:
            EventBus().publish('outbid_notification', {
                'recipient_id': str(user_id),
                'auction_id': str(instance.auction_id),
                'new_bid_amount': str(instance.amount),
                'vehicle_info': f"{instance.auction.vehicle.make} {instance.auction.vehicle.model} {instance.auction.vehicle.year}"
            })


@receiver(pre_save, sender=Bid)
def validate_bid(sender, instance, **kwargs):
    """Validar puja antes de guardar."""
    if not instance.pk:  # Solo para nuevas pujas
        # Verificar que la subasta esté activa
        if instance.auction.status != AuctionStatus.ACTIVE.value:
            raise ValueError("La subasta no está activa")
        
        # Verificar que no haya terminado
        if instance.auction.end_time <= timezone.now():
            raise ValueError("La subasta ha terminado")
        
        # Verificar que el usuario no sea el vendedor
        if instance.auction.seller_id == instance.bidder_id:
            raise ValueError("No puedes pujar en tu propia subasta")
        
        # Verificar que la cantidad sea mayor al precio actual
        if instance.amount <= instance.auction.current_price:
            raise ValueError(f"La puja debe ser mayor a {instance.auction.current_price}")


# Conectar señales de manera explícita
def connect_auction_signals():
    """Conectar todas las señales de subastas."""
    # Las señales ya están conectadas con @receiver
    pass
