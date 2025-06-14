"""
Infrastructure Services.
Implementaciones de servicios para la capa de infraestructura.
"""

import hashlib
import secrets
from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.users.domain.interfaces import (
    EmailServiceInterface,
    PasswordServiceInterface,
    UserEventPublisherInterface
)
from apps.users.domain.entities import UserEntity


class DjangoEmailService(EmailServiceInterface):
    """Servicio de email usando Django."""
    
    async def send_verification_email(self, user_email: str, token: str) -> bool:
        """Enviar email de verificación."""
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            subject = "Verifica tu cuenta - Logistics Template"
            html_message = render_to_string('emails/verification_email.html', {
                'verification_url': verification_url,
                'user_email': user_email,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            # Log error
            print(f"Error enviando email de verificación: {e}")
            return False
    
    async def send_password_reset_email(self, user_email: str, token: str) -> bool:
        """Enviar email de reset de contraseña."""
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            subject = "Restablecer contraseña - Logistics Template"
            html_message = render_to_string('emails/password_reset_email.html', {
                'reset_url': reset_url,
                'user_email': user_email,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            # Log error
            print(f"Error enviando email de reset: {e}")
            return False
    
    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Enviar email de bienvenida."""
        try:
            subject = "¡Bienvenido a Logistics Template!"
            html_message = render_to_string('emails/welcome_email.html', {
                'user_name': user_name,
                'user_email': user_email,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            # Log error
            print(f"Error enviando email de bienvenida: {e}")
            return False


class DjangoPasswordService(PasswordServiceInterface):
    """Servicio de contraseñas usando Django."""
    
    def hash_password(self, password: str) -> str:
        """Hashear contraseña usando Django."""
        return make_password(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verificar contraseña."""
        return check_password(password, hashed_password)
    
    def generate_reset_token(self, user_email: str) -> str:
        """Generar token de reset."""
        signer = TimestampSigner()
        return signer.sign(user_email)
    
    def verify_reset_token(self, token: str) -> Optional[str]:
        """Verificar token de reset y retornar email."""
        try:
            signer = TimestampSigner()
            # Token válido por 1 hora (3600 segundos)
            email = signer.unsign(token, max_age=3600)
            return email
        except (BadSignature, SignatureExpired):
            return None


class CeleryUserEventPublisher(UserEventPublisherInterface):
    """Publicador de eventos usando Celery."""
    
    async def publish_user_created(self, user: UserEntity) -> None:
        """Publicar evento de usuario creado."""
        from apps.users.infrastructure.tasks import handle_user_created
        handle_user_created.delay(str(user.id))
    
    async def publish_user_updated(self, user: UserEntity) -> None:
        """Publicar evento de usuario actualizado."""
        from apps.users.infrastructure.tasks import handle_user_updated
        handle_user_updated.delay(str(user.id))
    
    async def publish_user_deleted(self, user_id) -> None:
        """Publicar evento de usuario eliminado."""
        from apps.users.infrastructure.tasks import handle_user_deleted
        handle_user_deleted.delay(str(user_id))
    
    async def publish_user_logged_in(self, user: UserEntity) -> None:
        """Publicar evento de login."""
        from apps.users.infrastructure.tasks import handle_user_logged_in
        handle_user_logged_in.delay(str(user.id))
