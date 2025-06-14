"""
Authentication Domain Interfaces
Repository and service interfaces for authentication
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import (
    AuthenticationResult,
    LoginCredentials,
    RegistrationData,
    PasswordResetRequest,
    TokenPayload,
    UserSession,
    TwoFactorSetup,
    SecurityEvent
)


class IAuthenticationRepository(ABC):
    """Repository interface for authentication data"""
    
    @abstractmethod
    def create_user_session(self, session: UserSession) -> UserSession:
        """Create a new user session"""
        pass
    
    @abstractmethod
    def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session by ID"""
        pass
    
    @abstractmethod
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        pass
    
    @abstractmethod
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate user session"""
        pass
    
    @abstractmethod
    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for user"""
        pass
    
    @abstractmethod
    def log_security_event(self, event: SecurityEvent) -> SecurityEvent:
        """Log security event"""
        pass
    
    @abstractmethod
    def get_security_events(self, user_id: str, limit: int = 50) -> List[SecurityEvent]:
        """Get security events for user"""
        pass


class ITokenService(ABC):
    """Service interface for token management"""
    
    @abstractmethod
    def generate_access_token(self, payload: TokenPayload) -> str:
        """Generate access token"""
        pass
    
    @abstractmethod
    def generate_refresh_token(self, payload: TokenPayload) -> str:
        """Generate refresh token"""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[TokenPayload]:
        """Validate and decode token"""
        pass
    
    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        pass
    
    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        pass
    
    @abstractmethod
    def generate_password_reset_token(self, user_id: str) -> str:
        """Generate password reset token"""
        pass
    
    @abstractmethod
    def validate_password_reset_token(self, token: str) -> Optional[str]:
        """Validate password reset token and return user_id"""
        pass


class IPasswordService(ABC):
    """Service interface for password management"""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash password"""
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        pass
    
    @abstractmethod
    def validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        pass
    
    @abstractmethod
    def generate_secure_password(self, length: int = 12) -> str:
        """Generate secure password"""
        pass


class ITwoFactorService(ABC):
    """Service interface for two-factor authentication"""
    
    @abstractmethod
    def generate_secret(self) -> str:
        """Generate 2FA secret"""
        pass
    
    @abstractmethod
    def generate_qr_code(self, secret: str, user_email: str) -> str:
        """Generate QR code URL for 2FA setup"""
        pass
    
    @abstractmethod
    def verify_totp_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        pass
    
    @abstractmethod
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes"""
        pass
    
    @abstractmethod
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume backup code"""
        pass


class IAuthenticationService(ABC):
    """Service interface for authentication operations"""
    
    @abstractmethod
    def authenticate(self, credentials: LoginCredentials) -> AuthenticationResult:
        """Authenticate user"""
        pass
    
    @abstractmethod
    def register(self, data: RegistrationData) -> AuthenticationResult:
        """Register new user"""
        pass
    
    @abstractmethod
    def logout(self, session_id: str) -> bool:
        """Logout user"""
        pass
    
    @abstractmethod
    def logout_all_sessions(self, user_id: str) -> bool:
        """Logout all user sessions"""
        pass
    
    @abstractmethod
    def reset_password(self, request: PasswordResetRequest) -> bool:
        """Reset user password"""
        pass
    
    @abstractmethod
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        pass
    
    @abstractmethod
    def setup_two_factor(self, user_id: str) -> TwoFactorSetup:
        """Setup two-factor authentication"""
        pass
    
    @abstractmethod
    def enable_two_factor(self, user_id: str, totp_code: str) -> bool:
        """Enable two-factor authentication"""
        pass
    
    @abstractmethod
    def disable_two_factor(self, user_id: str, password: str) -> bool:
        """Disable two-factor authentication"""
        pass
