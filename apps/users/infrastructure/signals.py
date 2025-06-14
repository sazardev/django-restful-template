"""
User Django Signals.
Señales para manejar eventos automáticos del modelo de usuario.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crear perfil de usuario automáticamente cuando se crea un usuario.
    """
    if created:
        from apps.users.infrastructure.models import UserProfile
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Guardar perfil de usuario cuando se actualiza el usuario.
    """
    if hasattr(instance, 'profile'):
        instance.profile.updated_at = timezone.now()
        instance.profile.save()


@receiver(pre_save, sender=User)
def update_user_timestamp(sender, instance, **kwargs):
    """
    Actualizar timestamp de usuario antes de guardar.
    """
    if instance.pk:  # Si es una actualización
        instance.updated_at = timezone.now()


@receiver(post_save, sender=User)
def handle_user_status_change(sender, instance, created, **kwargs):
    """
    Manejar cambios en el estado del usuario.
    """
    if not created and instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Si el estado cambió a activo
            if (old_instance.status != 'active' and 
                instance.status == 'active' and 
                instance.is_email_verified):
                
                # Enviar email de bienvenida
                from apps.users.infrastructure.tasks import send_welcome_email_task
                send_welcome_email_task.delay(
                    instance.email, 
                    instance.get_full_name()
                )
            
            # Si el email fue verificado
            if (not old_instance.is_email_verified and 
                instance.is_email_verified):
                
                # Activar usuario si estaba pendiente
                if instance.status == 'pending_verification':
                    instance.status = 'active'
                    instance.save()
                
        except User.DoesNotExist:
            # Primera vez guardando el usuario
            pass


@receiver(post_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """
    Manejar eliminación de usuario.
    """
    # Log de auditoría
    from apps.audit.infrastructure.tasks import create_audit_log
    create_audit_log.delay(
        action="USER_DELETED",
        user_id=str(instance.id),
        details={
            "email": instance.email,
            "username": instance.username,
            "deleted_at": timezone.now().isoformat()
        }
    )
    
    # Notificar a administradores
    from apps.users.infrastructure.tasks import send_admin_notification
    send_admin_notification.delay(
        f"Usuario eliminado: {instance.get_full_name()} ({instance.email})"
    )
