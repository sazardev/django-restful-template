"""
Authentication Infrastructure Models
Django models for authentication and session management
"""

from django.db import models
from django.contrib.auth import get_user_model
from shared.infrastructure.models import BaseModel
import uuid

User = get_user_model()


class UserSession(BaseModel):
    """User session model for tracking active sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_fingerprint = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'auth_user_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f'Session {self.session_id[:8]}... for {self.user.username}'


class SecurityEvent(BaseModel):
    """Security events and audit log"""
    
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('logout_all_sessions', 'Logout All Sessions'),
        ('password_changed', 'Password Changed'),
        ('password_reset_requested', 'Password Reset Requested'),
        ('password_reset_completed', 'Password Reset Completed'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
        ('2fa_failed', '2FA Failed'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('user_registered', 'User Registered'),
        ('email_verified', 'Email Verified'),
        ('profile_updated', 'Profile Updated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    details = models.JSONField(default=dict)
    risk_score = models.FloatField(default=0.0)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'auth_security_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f'{self.event_type} - {self.user.username} at {self.created_at}'


class TwoFactorAuth(BaseModel):
    """Two-factor authentication setup for users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    secret_key = models.CharField(max_length=32)
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list)  # List of backup codes
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_two_factor'
    
    def __str__(self):
        return f'2FA for {self.user.username} ({"Enabled" if self.is_enabled else "Disabled"})'


class PasswordResetToken(BaseModel):
    """Password reset tokens"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        db_table = 'auth_password_reset_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f'Reset token for {self.user.username}'


class EmailVerificationToken(BaseModel):
    """Email verification tokens"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    email = models.EmailField()
    token = models.CharField(max_length=255, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_email_verification_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f'Email verification for {self.email}'


class RevokedToken(BaseModel):
    """Revoked JWT tokens for blacklisting"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jti = models.CharField(max_length=255, unique=True, db_index=True)  # JWT ID
    token_type = models.CharField(max_length=20)  # 'access' or 'refresh'
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revoked_tokens')
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_revoked_tokens'
        indexes = [
            models.Index(fields=['jti']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['user', 'token_type']),
        ]
    
    def __str__(self):
        return f'Revoked {self.token_type} token ({self.jti[:8]}...)'


class LoginAttempt(BaseModel):
    """Failed login attempts for rate limiting and security"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(db_index=True)
    username_or_email = models.CharField(max_length=255, db_index=True)
    user_agent = models.TextField()
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'auth_login_attempts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['username_or_email', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]
    
    def __str__(self):
        return f'Login attempt for {self.username_or_email} from {self.ip_address}'
