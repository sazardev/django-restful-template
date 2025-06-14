"""
Authentication API Serializers
REST API serializers for authentication endpoints
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    identifier = serializers.CharField(
        max_length=255,
        help_text="Username or email address"
    )
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    remember_me = serializers.BooleanField(default=False)
    two_factor_code = serializers.CharField(
        max_length=6,
        required=False,
        allow_blank=True,
        help_text="Six-digit TOTP code or backup code"
    )
    
    def validate_identifier(self, value):
        """Validate identifier format"""
        if not value.strip():
            raise serializers.ValidationError("Identifier cannot be empty")
        return value.strip().lower()


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration"""
    
    username = serializers.CharField(
        max_length=150,
        min_length=3,
        help_text="3-150 characters. Letters, digits and @/./+/-/_ only."
    )
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    terms_accepted = serializers.BooleanField()
    marketing_consent = serializers.BooleanField(default=False)
    
    def validate_username(self, value):
        """Validate username"""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        """Validate email"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value.lower()
    
    def validate_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate_terms_accepted(self, value):
        """Validate terms acceptance"""
        if not value:
            raise serializers.ValidationError("You must accept the terms and conditions")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation does not match'
            })
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists"""
        # Always return success to prevent email enumeration
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    token = serializers.CharField(max_length=255)
    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                'new_password_confirm': 'Password confirmation does not match'
            })
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                'new_password_confirm': 'Password confirmation does not match'
            })
        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    
    refresh = serializers.CharField()


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup response"""
    
    secret_key = serializers.CharField(read_only=True)
    qr_code_url = serializers.CharField(read_only=True)
    backup_codes = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )


class TwoFactorEnableSerializer(serializers.Serializer):
    """Serializer for enabling 2FA"""
    
    totp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="Six-digit TOTP code from authenticator app"
    )


class TwoFactorDisableSerializer(serializers.Serializer):
    """Serializer for disabling 2FA"""
    
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )


class UserSessionSerializer(serializers.Serializer):
    """Serializer for user session information"""
    
    session_id = serializers.CharField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_activity = serializers.DateTimeField(read_only=True)
    is_current = serializers.BooleanField(read_only=True)


class SecurityEventSerializer(serializers.Serializer):
    """Serializer for security events"""
    
    event_type = serializers.CharField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    details = serializers.JSONField(read_only=True)
    risk_score = serializers.FloatField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class AuthenticationResponseSerializer(serializers.Serializer):
    """Serializer for authentication response"""
    
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
    token_type = serializers.CharField(read_only=True, default='Bearer')
    user = serializers.SerializerMethodField()
    requires_2fa = serializers.BooleanField(read_only=True, default=False)
    
    def get_user(self, obj):
        """Get basic user information"""
        if hasattr(obj, 'user_id') and obj.user_id:
            try:
                user = User.objects.get(id=obj.user_id)
                return {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined,
                }
            except User.DoesNotExist:
                pass
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'username', 'is_staff', 'is_active', 'date_joined', 'last_login'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        user = self.context['request'].user
        if User.objects.filter(email__iexact=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already in use")
        return value.lower()
