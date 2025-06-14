"""
User Domain Interfaces.
Interfaces para el sistema de usuarios siguiendo principios SOLID.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from apps.users.domain.entities import UserEntity


class UserRepositoryInterface(ABC):
    """Interface para el repositorio de usuarios."""
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Obtener usuario por ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Obtener usuario por email."""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Obtener usuario por username."""
        pass
    
    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        """Crear un nuevo usuario."""
        pass
    
    @abstractmethod
    async def update(self, user: UserEntity) -> UserEntity:
        """Actualizar usuario existente."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Eliminar usuario."""
        pass
    
    @abstractmethod
    async def list_users(
        self, 
        limit: int = 20, 
        offset: int = 0,
        filters: Optional[dict] = None
    ) -> List[UserEntity]:
        """Listar usuarios con filtros."""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[dict] = None) -> int:
        """Contar usuarios."""
        pass


class EmailServiceInterface(ABC):
    """Interface para servicio de email."""
    
    @abstractmethod
    async def send_verification_email(self, user_email: str, token: str) -> bool:
        """Enviar email de verificación."""
        pass
    
    @abstractmethod
    async def send_password_reset_email(self, user_email: str, token: str) -> bool:
        """Enviar email de reset de contraseña."""
        pass
    
    @abstractmethod
    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Enviar email de bienvenida."""
        pass


class PasswordServiceInterface(ABC):
    """Interface para servicio de contraseñas."""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hashear contraseña."""
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verificar contraseña."""
        pass
    
    @abstractmethod
    def generate_reset_token(self, user_email: str) -> str:
        """Generar token de reset."""
        pass
    
    @abstractmethod
    def verify_reset_token(self, token: str) -> Optional[str]:
        """Verificar token de reset y retornar email."""
        pass


class UserEventPublisherInterface(ABC):
    """Interface para publicar eventos de usuario."""
    
    @abstractmethod
    async def publish_user_created(self, user: UserEntity) -> None:
        """Publicar evento de usuario creado."""
        pass
    
    @abstractmethod
    async def publish_user_updated(self, user: UserEntity) -> None:
        """Publicar evento de usuario actualizado."""
        pass
    
    @abstractmethod
    async def publish_user_deleted(self, user_id: UUID) -> None:
        """Publicar evento de usuario eliminado."""
        pass
    
    @abstractmethod
    async def publish_user_logged_in(self, user: UserEntity) -> None:
        """Publicar evento de login."""
        pass
