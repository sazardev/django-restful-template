"""
User Domain Models.
Entidades de dominio para el sistema de usuarios.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID


class UserRole(Enum):
    """Roles de usuario en el sistema."""
    SUPER_ADMIN = "super_admin"
    LOGISTICS_MANAGER = "logistics_manager"
    FLEET_MANAGER = "fleet_manager"
    AUCTION_MANAGER = "auction_manager"
    DRIVER = "driver"
    CLIENT = "client"


class UserStatus(Enum):
    """Estados de usuario."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass(frozen=True)
class UserProfile:
    """Perfil de usuario - Value Object."""
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    avatar: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class UserEntity:
    """Entidad de usuario del dominio."""
    id: UUID
    email: str
    username: str
    profile: UserProfile
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    groups: List[str] = None
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.groups is None:
            self.groups = []
        if self.permissions is None:
            self.permissions = []
    
    def activate(self) -> None:
        """Activar usuario."""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Desactivar usuario."""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.now()
    
    def suspend(self) -> None:
        """Suspender usuario."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.now()
    
    def verify_email(self) -> None:
        """Verificar email del usuario."""
        self.is_email_verified = True
        self.updated_at = datetime.now()
    
    def can_access_resource(self, resource: str) -> bool:
        """Verificar si el usuario puede acceder a un recurso."""
        # Lógica de negocio para permisos
        if self.role == UserRole.SUPER_ADMIN:
            return True
        
        role_permissions = {
            UserRole.LOGISTICS_MANAGER: [
                'view_logistics', 'manage_logistics', 'view_reports'
            ],
            UserRole.FLEET_MANAGER: [
                'view_vehicles', 'manage_vehicles', 'view_tracking'
            ],
            UserRole.AUCTION_MANAGER: [
                'view_auctions', 'manage_auctions', 'create_auctions'
            ],
            UserRole.DRIVER: [
                'view_own_vehicles', 'update_location'
            ],
            UserRole.CLIENT: [
                'view_auctions', 'place_bids', 'view_own_orders'
            ]
        }
        
        allowed_permissions = role_permissions.get(self.role, [])
        return resource in allowed_permissions or resource in self.permissions
    
    def is_active_user(self) -> bool:
        """Verificar si el usuario está activo."""
        return self.status == UserStatus.ACTIVE and self.is_email_verified
