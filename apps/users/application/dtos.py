"""
User Application DTOs.
Data Transfer Objects para la capa de aplicación.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from apps.users.domain.entities import UserRole, UserStatus


@dataclass
class CreateUserCommand:
    """Comando para crear usuario."""
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
    role: UserRole
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


@dataclass
class UpdateUserCommand:
    """Comando para actualizar usuario."""
    user_id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    avatar: Optional[str] = None


@dataclass
class ChangeUserRoleCommand:
    """Comando para cambiar rol de usuario."""
    user_id: UUID
    new_role: UserRole
    performed_by: UUID


@dataclass
class ChangeUserStatusCommand:
    """Comando para cambiar estado de usuario."""
    user_id: UUID
    new_status: UserStatus
    reason: Optional[str] = None
    performed_by: Optional[UUID] = None


@dataclass
class UserQuery:
    """Query para buscar usuarios."""
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    search: Optional[str] = None
    limit: int = 20
    offset: int = 0


@dataclass
class UserDTO:
    """DTO de usuario para respuestas."""
    id: UUID
    email: str
    username: str
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    status: UserStatus
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    avatar: Optional[str]
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    groups: List[str]
    permissions: List[str]


@dataclass
class LoginCommand:
    """Comando para login."""
    email_or_username: str
    password: str
    remember_me: bool = False


@dataclass
class LoginResponse:
    """Respuesta de login."""
    user: UserDTO
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass
class PasswordResetCommand:
    """Comando para reset de contraseña."""
    email: str


@dataclass
class ConfirmPasswordResetCommand:
    """Comando para confirmar reset de contraseña."""
    token: str
    new_password: str


@dataclass
class ChangePasswordCommand:
    """Comando para cambiar contraseña."""
    user_id: UUID
    current_password: str
    new_password: str


@dataclass
class VerifyEmailCommand:
    """Comando para verificar email."""
    token: str
