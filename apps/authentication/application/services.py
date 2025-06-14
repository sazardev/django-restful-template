"""
Authentication Application Services
Use cases and business logic for authentication
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from ..domain.entities import (
    AuthenticationResult,
    LoginCredentials,
    RegistrationData,
    PasswordResetRequest,
    TokenPayload,
    UserSession,
    TwoFactorSetup,
    SecurityEvent,
    AuthenticationMethod,
    TokenType
)
from ..domain.interfaces import (
    IAuthenticationRepository,
    ITokenService,
    IPasswordService,
    ITwoFactorService,
    IAuthenticationService
)

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationApplicationService(IAuthenticationService):
    """
    Application service for authentication operations
    Orchestrates domain services and repositories to implement use cases
    """
    
    def __init__(
        self,
        auth_repository: IAuthenticationRepository,
        token_service: ITokenService,
        password_service: IPasswordService,
        two_factor_service: ITwoFactorService
    ):
        self.auth_repository = auth_repository
        self.token_service = token_service
        self.password_service = password_service
        self.two_factor_service = two_factor_service
    
    @transaction.atomic
    def authenticate(self, credentials: LoginCredentials) -> AuthenticationResult:
        """
        Authenticate user with credentials
        
        Args:
            credentials: User login credentials
            
        Returns:
            AuthenticationResult with tokens if successful
        """
        try:
            # Find user by identifier (email or username)
            user = self._find_user(credentials.identifier)
            if not user:
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            # Verify password
            if not self.password_service.verify_password(credentials.password, user.password):
                self._log_security_event(
                    user.id,
                    "login_failed",
                    {"reason": "invalid_password"}
                )
                return AuthenticationResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            # Check if user is active
            if not user.is_active:
                return AuthenticationResult(
                    success=False,
                    error_message="Account is deactivated"
                )
            
            # Check 2FA requirement
            if hasattr(user, 'two_factor_enabled') and user.two_factor_enabled:
                if not credentials.two_factor_code:
                    return AuthenticationResult(
                        success=False,
                        requires_2fa=True,
                        error_message="Two-factor authentication required"
                    )
                
                # Verify 2FA code
                if not self._verify_2fa_code(user, credentials.two_factor_code):
                    self._log_security_event(
                        user.id,
                        "2fa_failed",
                        {"code_provided": bool(credentials.two_factor_code)}
                    )
                    return AuthenticationResult(
                        success=False,
                        error_message="Invalid two-factor code"
                    )
            
            # Create session
            session = self._create_user_session(user, credentials)
            
            # Generate tokens
            token_payload = TokenPayload(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                roles=list(user.groups.values_list('name', flat=True)),
                permissions=list(user.user_permissions.values_list('codename', flat=True)),
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                token_type=TokenType.ACCESS,
                session_id=session.session_id
            )
            
            access_token = self.token_service.generate_access_token(token_payload)
            refresh_token = self.token_service.generate_refresh_token(token_payload)
            
            # Log successful login
            self._log_security_event(
                user.id,
                "login_success",
                {
                    "method": credentials.method.value,
                    "session_id": session.session_id
                }
            )
            
            return AuthenticationResult(
                success=True,
                user_id=str(user.id),
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600,  # 1 hour
                session_id=session.session_id
            )
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return AuthenticationResult(
                success=False,
                error_message="Authentication failed"
            )
    
    @transaction.atomic
    def register(self, data: RegistrationData) -> AuthenticationResult:
        """
        Register new user
        
        Args:
            data: User registration data
            
        Returns:
            AuthenticationResult with tokens if successful
        """
        try:
            # Validate password strength
            if not self.password_service.validate_password_strength(data.password):
                return AuthenticationResult(
                    success=False,
                    error_message="Password does not meet security requirements"
                )
            
            # Check if user already exists
            if User.objects.filter(email=data.email).exists():
                return AuthenticationResult(
                    success=False,
                    error_message="Email already registered"
                )
            
            if User.objects.filter(username=data.username).exists():
                return AuthenticationResult(
                    success=False,
                    error_message="Username already taken"
                )
            
            # Hash password
            hashed_password = self.password_service.hash_password(data.password)
            
            # Create user
            user = User.objects.create(
                username=data.username,
                email=data.email,
                password=hashed_password,
                first_name=data.first_name or '',
                last_name=data.last_name or '',
                is_active=True
            )
            
            # Log registration
            self._log_security_event(
                user.id,
                "user_registered",
                {"email": data.email, "username": data.username}
            )
            
            # Automatically authenticate the new user
            credentials = LoginCredentials(
                identifier=data.email,
                password=data.password,
                method=AuthenticationMethod.EMAIL_PASSWORD
            )
            
            return self.authenticate(credentials)
            
        except ValidationError as e:
            return AuthenticationResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return AuthenticationResult(
                success=False,
                error_message="Registration failed"
            )
    
    def logout(self, session_id: str) -> bool:
        """Logout user session"""
        try:
            success = self.auth_repository.deactivate_session(session_id)
            if success:
                # Get session info for logging
                session = self.auth_repository.get_user_session(session_id)
                if session:
                    self._log_security_event(
                        session.user_id,
                        "logout",
                        {"session_id": session_id}
                    )
            return success
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    def logout_all_sessions(self, user_id: str) -> bool:
        """Logout all user sessions"""
        try:
            sessions = self.auth_repository.get_user_sessions(user_id)
            success = True
            
            for session in sessions:
                if not self.auth_repository.deactivate_session(session.session_id):
                    success = False
            
            if success:
                self._log_security_event(
                    user_id,
                    "logout_all_sessions",
                    {"session_count": len(sessions)}
                )
            
            return success
        except Exception as e:
            logger.error(f"Logout all sessions error: {str(e)}")
            return False
    
    @transaction.atomic
    def reset_password(self, request: PasswordResetRequest) -> bool:
        """Reset user password"""
        try:
            if request.token and request.new_password:
                # Verify reset token
                user_id = self.token_service.validate_password_reset_token(request.token)
                if not user_id:
                    return False
                
                # Validate new password
                if not self.password_service.validate_password_strength(request.new_password):
                    return False
                
                # Update password
                user = User.objects.get(id=user_id)
                user.password = self.password_service.hash_password(request.new_password)
                user.save()
                
                # Logout all sessions for security
                self.logout_all_sessions(user_id)
                
                # Log password reset
                self._log_security_event(
                    user_id,
                    "password_reset_completed",
                    {"email": user.email}
                )
                
                return True
            else:
                # Generate reset token and send email
                user = User.objects.filter(email=request.email).first()
                if user:
                    token = self.token_service.generate_password_reset_token(str(user.id))
                    # TODO: Send email with reset token
                    self._log_security_event(
                        user.id,
                        "password_reset_requested",
                        {"email": request.email}
                    )
                return True  # Always return True to prevent email enumeration
                
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return False
    
    @transaction.atomic
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = User.objects.get(id=user_id)
            
            # Verify old password
            if not self.password_service.verify_password(old_password, user.password):
                return False
            
            # Validate new password
            if not self.password_service.validate_password_strength(new_password):
                return False
            
            # Update password
            user.password = self.password_service.hash_password(new_password)
            user.save()
            
            # Log password change
            self._log_security_event(
                user_id,
                "password_changed",
                {"email": user.email}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Change password error: {str(e)}")
            return False
    
    def setup_two_factor(self, user_id: str) -> TwoFactorSetup:
        """Setup two-factor authentication for user"""
        try:
            user = User.objects.get(id=user_id)
            
            # Generate secret and QR code
            secret = self.two_factor_service.generate_secret()
            qr_code_url = self.two_factor_service.generate_qr_code(secret, user.email)
            backup_codes = self.two_factor_service.generate_backup_codes()
            
            return TwoFactorSetup(
                user_id=user_id,
                secret_key=secret,
                qr_code_url=qr_code_url,
                backup_codes=backup_codes,
                is_enabled=False
            )
            
        except Exception as e:
            logger.error(f"2FA setup error: {str(e)}")
            raise
    
    def enable_two_factor(self, user_id: str, totp_code: str) -> bool:
        """Enable two-factor authentication"""
        try:
            # Verify TOTP code
            # This would need to get the secret from setup process
            # Implementation depends on how you store the setup data
            
            self._log_security_event(
                user_id,
                "2fa_enabled",
                {}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"2FA enable error: {str(e)}")
            return False
    
    def disable_two_factor(self, user_id: str, password: str) -> bool:
        """Disable two-factor authentication"""
        try:
            user = User.objects.get(id=user_id)
            
            # Verify password
            if not self.password_service.verify_password(password, user.password):
                return False
            
            # Disable 2FA (implementation depends on your user model)
            
            self._log_security_event(
                user_id,
                "2fa_disabled",
                {}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"2FA disable error: {str(e)}")
            return False
    
    def _find_user(self, identifier: str) -> Optional[User]:
        """Find user by email or username"""
        try:
            if '@' in identifier:
                return User.objects.get(email=identifier)
            else:
                return User.objects.get(username=identifier)
        except User.DoesNotExist:
            return None
    
    def _create_user_session(self, user: User, credentials: LoginCredentials) -> UserSession:
        """Create user session"""
        import uuid
        
        session = UserSession(
            session_id=str(uuid.uuid4()),
            user_id=str(user.id),
            ip_address="127.0.0.1",  # TODO: Get from request
            user_agent="Unknown",  # TODO: Get from request
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            is_active=True
        )
        
        return self.auth_repository.create_user_session(session)
    
    def _verify_2fa_code(self, user: User, code: str) -> bool:
        """Verify 2FA code"""
        # Implementation depends on how you store 2FA secrets
        # This is a placeholder
        return True
    
    def _log_security_event(self, user_id: str, event_type: str, details: dict):
        """Log security event"""
        event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address="127.0.0.1",  # TODO: Get from request
            user_agent="Unknown",  # TODO: Get from request
            details=details,
            created_at=datetime.utcnow()
        )
        
        self.auth_repository.log_security_event(event)
