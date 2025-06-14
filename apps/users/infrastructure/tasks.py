"""
User Celery Tasks.
Tareas asíncronas para el sistema de usuarios.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@shared_task
def handle_user_created(user_id: str):
    """
    Manejar evento de usuario creado.
    Ejecuta acciones posteriores a la creación de un usuario.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Crear perfil de usuario si no existe
        if not hasattr(user, 'profile'):
            from apps.users.infrastructure.models import UserProfile
            UserProfile.objects.create(user=user)
        
        # Enviar notificación a administradores
        send_admin_notification.delay(
            f"Nuevo usuario registrado: {user.get_full_name()} ({user.email})"
        )
        
        # Log de auditoría
        from apps.audit.infrastructure.tasks import create_audit_log
        create_audit_log.delay(
            action="USER_CREATED",
            user_id=str(user.id),
            details={
                "email": user.email,
                "username": user.username,
                "role": user.role
            }
        )
        
        return f"Usuario {user_id} procesado correctamente"
    
    except User.DoesNotExist:
        return f"Usuario {user_id} no encontrado"
    except Exception as e:
        return f"Error procesando usuario {user_id}: {str(e)}"


@shared_task
def handle_user_updated(user_id: str):
    """
    Manejar evento de usuario actualizado.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Actualizar timestamp de última actividad en el perfil
        if hasattr(user, 'profile'):
            user.profile.last_activity = timezone.now()
            user.profile.save()
        
        # Log de auditoría
        from apps.audit.infrastructure.tasks import create_audit_log
        create_audit_log.delay(
            action="USER_UPDATED",
            user_id=str(user.id),
            details={
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "status": user.status
            }
        )
        
        return f"Actualización de usuario {user_id} procesada"
    
    except User.DoesNotExist:
        return f"Usuario {user_id} no encontrado"
    except Exception as e:
        return f"Error procesando actualización de usuario {user_id}: {str(e)}"


@shared_task
def handle_user_deleted(user_id: str):
    """
    Manejar evento de usuario eliminado.
    """
    try:
        # Log de auditoría
        from apps.audit.infrastructure.tasks import create_audit_log
        create_audit_log.delay(
            action="USER_DELETED",
            user_id=user_id,
            details={
                "deleted_at": timezone.now().isoformat()
            }
        )
        
        # Notificar a administradores
        send_admin_notification.delay(
            f"Usuario eliminado: {user_id}"
        )
        
        return f"Eliminación de usuario {user_id} procesada"
    
    except Exception as e:
        return f"Error procesando eliminación de usuario {user_id}: {str(e)}"


@shared_task
def handle_user_logged_in(user_id: str):
    """
    Manejar evento de login de usuario.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Actualizar último login y actividad
        user.last_login = timezone.now()
        user.save()
        
        if hasattr(user, 'profile'):
            user.profile.last_activity = timezone.now()
            user.profile.save()
        
        # Log de auditoría
        from apps.audit.infrastructure.tasks import create_audit_log
        create_audit_log.delay(
            action="USER_LOGIN",
            user_id=str(user.id),
            details={
                "login_time": timezone.now().isoformat(),
                "email": user.email
            }
        )
        
        return f"Login de usuario {user_id} procesado"
    
    except User.DoesNotExist:
        return f"Usuario {user_id} no encontrado"
    except Exception as e:
        return f"Error procesando login de usuario {user_id}: {str(e)}"


@shared_task
def send_admin_notification(message: str):
    """
    Enviar notificación a administradores.
    """
    try:
        from django.core.mail import mail_admins
        
        mail_admins(
            subject="Notificación del Sistema - Logistics Template",
            message=message,
            fail_silently=False
        )
        
        return f"Notificación enviada: {message}"
    
    except Exception as e:
        return f"Error enviando notificación: {str(e)}"


@shared_task
def cleanup_unverified_users():
    """
    Limpiar usuarios no verificados después de 7 días.
    Esta tarea se ejecuta periódicamente.
    """
    from datetime import timedelta
    
    try:
        cutoff_date = timezone.now() - timedelta(days=7)
        
        unverified_users = User.objects.filter(
            is_email_verified=False,
            created_at__lt=cutoff_date,
            status='pending_verification'
        )
        
        count = unverified_users.count()
        unverified_users.delete()
        
        # Log de auditoría
        from apps.audit.infrastructure.tasks import create_audit_log
        create_audit_log.delay(
            action="CLEANUP_UNVERIFIED_USERS",
            user_id=None,
            details={
                "deleted_count": count,
                "cutoff_date": cutoff_date.isoformat()
            }
        )
        
        return f"Eliminados {count} usuarios no verificados"
    
    except Exception as e:
        return f"Error en limpieza de usuarios: {str(e)}"


@shared_task
def send_user_statistics_report():
    """
    Enviar reporte estadístico de usuarios.
    Se ejecuta diariamente.
    """
    try:
        from django.db.models import Count
        from django.core.mail import mail_admins
        
        # Estadísticas de usuarios
        total_users = User.objects.count()
        active_users = User.objects.filter(status='active').count()
        pending_users = User.objects.filter(status='pending_verification').count()
        
        # Usuarios por rol
        role_stats = User.objects.values('role').annotate(count=Count('role'))
        
        # Crear reporte
        report = f"""
        Reporte Diario de Usuarios - {timezone.now().strftime('%Y-%m-%d')}
        
        Total de usuarios: {total_users}
        Usuarios activos: {active_users}
        Usuarios pendientes: {pending_users}
        
        Distribución por rol:
        """
        
        for stat in role_stats:
            report += f"- {stat['role']}: {stat['count']}\n"
        
        # Enviar por email
        mail_admins(
            subject="Reporte Diario de Usuarios",
            message=report,
            fail_silently=False
        )
        
        return "Reporte de estadísticas enviado"
    
    except Exception as e:
        return f"Error generando reporte: {str(e)}"
