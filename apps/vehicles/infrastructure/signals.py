"""
Vehicle Infrastructure Signals
Django signals for vehicle-related events
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Vehicle
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Vehicle)
def vehicle_saved(sender, instance, created, **kwargs):
    """Handle vehicle save events"""
    if created:
        logger.info(f"New vehicle created: {instance.license_plate}")
        # TODO: Send notification, update cache, etc.
    else:
        logger.info(f"Vehicle updated: {instance.license_plate}")
        # TODO: Handle vehicle updates


@receiver(post_delete, sender=Vehicle)
def vehicle_deleted(sender, instance, **kwargs):
    """Handle vehicle delete events"""
    logger.info(f"Vehicle deleted: {instance.license_plate}")
    # TODO: Cleanup related data, send notifications, etc.
