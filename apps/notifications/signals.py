"""
Notification Signals.
Señales para la aplicación de notificaciones.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.notifications.infrastructure.models import NotificationModel
from apps.notifications.application.services import NotificationApplicationService

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=NotificationModel)
def notification_created(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta cuando se crea una nueva notificación.
    Puede enviar la notificación en tiempo real si está configurado.
    """
    if created:
        logger.info(f"Nueva notificación creada: {instance.id} para usuario {instance.user.email}")
        
        # Aquí puedes agregar lógica adicional como:
        # - Envío de emails
        # - Envío de push notifications
        # - Logging adicional
        # - Integración con servicios externos


@receiver(post_save, sender=User)
def user_created_notification(sender, instance, created, **kwargs):
    """
    Signal que envía una notificación de bienvenida cuando se crea un nuevo usuario.
    """
    if created:
        try:
            service = NotificationApplicationService()
            service.create_notification(
                user_id=instance.id,
                title="¡Bienvenido al sistema!",
                message=f"Hola {instance.first_name or instance.email}, bienvenido a nuestro sistema de gestión logística. "
                       f"Aquí podrás participar en subastas de vehículos y gestionar tus operaciones.",
                notification_type="success",
                priority=2,  # Normal
                data={
                    'user_type': 'new_user',
                    'welcome_message': True,
                    'action_required': False
                },
                expires_in_hours=168,  # 1 semana
                send_realtime=True
            )
            logger.info(f"Notificación de bienvenida enviada al usuario: {instance.email}")
        except Exception as e:
            logger.error(f"Error enviando notificación de bienvenida: {e}")


# Importar señales de otras apps para notificaciones
try:
    from apps.auctions.infrastructure.models import AuctionModel, BidModel
    
    @receiver(post_save, sender=AuctionModel)
    def auction_created_notification(sender, instance, created, **kwargs):
        """
        Signal que notifica cuando se crea una nueva subasta.
        """
        if created:
            try:
                from apps.notifications.application.services import NotificationAuctionService
                
                service = NotificationAuctionService()
                # TODO: Implementar lógica para notificar a usuarios interesados
                # service.notify_auction_created({...})
                
                logger.info(f"Subasta creada, notificaciones enviadas: {instance.id}")
            except Exception as e:
                logger.error(f"Error enviando notificaciones de subasta creada: {e}")
    
    @receiver(post_save, sender=BidModel)
    def bid_created_notification(sender, instance, created, **kwargs):
        """
        Signal que notifica cuando se crea una nueva puja.
        """
        if created:
            try:
                from apps.notifications.application.services import NotificationAuctionService
                
                service = NotificationAuctionService()
                
                # Obtener puja anterior
                previous_bid = BidModel.objects.filter(
                    auction=instance.auction,
                    created_at__lt=instance.created_at
                ).order_by('-amount').first()
                
                previous_bidder_id = previous_bid.bidder.id if previous_bid else None
                
                service.notify_new_bid(
                    auction_id=instance.auction.id,
                    bidder_id=instance.bidder.id,
                    previous_bidder_id=previous_bidder_id,
                    bid_amount=float(instance.amount)
                )
                
                logger.info(f"Notificación de nueva puja enviada: {instance.id}")
            except Exception as e:
                logger.error(f"Error enviando notificación de nueva puja: {e}")

except ImportError:
    logger.warning("No se pudieron importar modelos de subastas para las señales")


try:
    from apps.vehicles.infrastructure.models import VehicleModel
    
    @receiver(post_save, sender=VehicleModel)
    def vehicle_created_notification(sender, instance, created, **kwargs):
        """
        Signal que notifica cuando se crea un nuevo vehículo.
        """
        if created:
            try:
                service = NotificationApplicationService()
                
                # Notificar al propietario
                service.create_notification(
                    user_id=instance.owner.id,
                    title="Vehículo registrado exitosamente",
                    message=f"Tu vehículo {instance.make} {instance.model} ({instance.year}) "
                           f"ha sido registrado en el sistema con VIN: {instance.vin}",
                    notification_type="success",
                    priority=2,  # Normal
                    data={
                        'vehicle_id': str(instance.id),
                        'vehicle_type': instance.vehicle_type,
                        'action': 'vehicle_created'
                    },
                    send_realtime=True
                )
                
                logger.info(f"Notificación de vehículo creado enviada: {instance.id}")
            except Exception as e:
                logger.error(f"Error enviando notificación de vehículo creado: {e}")

except ImportError:
    logger.warning("No se pudieron importar modelos de vehículos para las señales")


@receiver(pre_delete, sender=NotificationModel)
def notification_deleted(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de eliminar una notificación.
    Útil para logging y auditoría.
    """
    logger.info(f"Notificación eliminada: {instance.id} del usuario {instance.user.email}")


# Signal para limpiar notificaciones expiradas (se puede ejecutar con cron o celery)
def cleanup_expired_notifications():
    """
    Función para limpiar notificaciones expiradas.
    Debe ser llamada por un trabajo programado.
    """
    try:
        service = NotificationApplicationService()
        count = service.cleanup_expired_notifications()
        logger.info(f"Limpieza de notificaciones expiradas: {count} eliminadas")
        return count
    except Exception as e:
        logger.error(f"Error en limpieza de notificaciones expiradas: {e}")
        return 0
