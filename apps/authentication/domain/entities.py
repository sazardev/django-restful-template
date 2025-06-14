"""
Authentication Domain Entities
Core business entities for authentication and authorization
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TokenType(Enum):
    """Token types for authentication"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class AuthenticationMethod(Enum):
    """Authentication methods supported"""
    EMAIL_PASSWORD = "email_password"
    USERNAME_PASSWORD = "username_password"
    GOOGLE_OAUTH = "google_oauth"
    GITHUB_OAUTH = "github_oauth"
    TWO_FACTOR = "two_factor"


@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    success: bool
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    error_message: Optional[str] = None
    requires_2fa: bool = False
    session_id: Optional[str] = None


@dataclass
class LoginCredentials:
    """User login credentials"""
    identifier: str  # username or email
    password: str
    method: AuthenticationMethod = AuthenticationMethod.EMAIL_PASSWORD
    remember_me: bool = False
    two_factor_code: Optional[str] = None


@dataclass
class RegistrationData:
    """User registration data"""
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    terms_accepted: bool = False
    marketing_consent: bool = False


@dataclass
class PasswordResetRequest:
    """Password reset request data"""
    email: str
    token: Optional[str] = None
    new_password: Optional[str] = None


@dataclass
class TokenPayload:
    """JWT token payload"""
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    issued_at: datetime
    expires_at: datetime
    token_type: TokenType
    session_id: Optional[str] = None


@dataclass
class UserSession:
    """User session information"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_active: bool = True
    device_fingerprint: Optional[str] = None
    location: Optional[str] = None


@dataclass
class TwoFactorSetup:
    """Two-factor authentication setup"""
    user_id: str
    secret_key: str
    qr_code_url: str
    backup_codes: List[str]
    is_enabled: bool = False


@dataclass
class SecurityEvent:
    """Security-related event"""
    user_id: str
    event_type: str
    ip_address: str
    user_agent: str
    details: dict
    created_at: datetime
    risk_score: float = 0.0
