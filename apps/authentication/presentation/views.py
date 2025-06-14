"""
Authentication API Views
REST API endpoints for authentication and user management
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from ..application.services import AuthenticationApplicationService
from ..domain.entities import (
    LoginCredentials,
    RegistrationData,
    PasswordResetRequest,
    AuthenticationMethod
)
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    RefreshTokenSerializer,
    TwoFactorSetupSerializer,
    TwoFactorEnableSerializer,
    TwoFactorDisableSerializer,
    UserSessionSerializer,
    SecurityEventSerializer,
    AuthenticationResponseSerializer,
    UserProfileSerializer
)

User = get_user_model()


class AuthenticationViewSet(GenericViewSet):
    """
    ViewSet for authentication operations
    
    Provides endpoints for:
    - Login/Logout
    - Registration
    - Password reset
    - Token refresh
    - Two-factor authentication
    - User sessions management
    - Security events
    """
    
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # In real implementation, you would inject dependencies properly
        # This is a simplified version for the template
        self.auth_service = None  # AuthenticationApplicationService()
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        User login endpoint
        
        POST /auth/login/
        Body: {
            "identifier": "user@example.com",
            "password": "password123",
            "remember_me": false,
            "two_factor_code": "123456"
        }
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create credentials from validated data
        credentials = LoginCredentials(
            identifier=serializer.validated_data['identifier'],
            password=serializer.validated_data['password'],
            method=AuthenticationMethod.EMAIL_PASSWORD,
            remember_me=serializer.validated_data.get('remember_me', False),
            two_factor_code=serializer.validated_data.get('two_factor_code')
        )
        
        # Authenticate user
        result = self.auth_service.authenticate(credentials)
        
        if result.success:
            response_serializer = AuthenticationResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'error': result.error_message,
                    'requires_2fa': result.requires_2fa
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        User registration endpoint
        
        POST /auth/register/
        Body: {
            "username": "newuser",
            "email": "user@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "first_name": "John",
            "last_name": "Doe",
            "terms_accepted": true
        }
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create registration data
        registration_data = RegistrationData(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name'),
            last_name=serializer.validated_data.get('last_name'),
            phone_number=serializer.validated_data.get('phone_number'),
            terms_accepted=serializer.validated_data['terms_accepted'],
            marketing_consent=serializer.validated_data.get('marketing_consent', False)
        )
        
        # Register user
        result = self.auth_service.register(registration_data)
        
        if result.success:
            response_serializer = AuthenticationResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': result.error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        User logout endpoint
        
        POST /auth/logout/
        """
        # Get session ID from token or request
        session_id = getattr(request.user, 'session_id', None)
        
        if session_id:
            success = self.auth_service.logout(session_id)
            if success:
                return Response({'message': 'Logged out successfully'})
        
        return Response(
            {'error': 'Logout failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout_all(self, request):
        """
        Logout all user sessions
        
        POST /auth/logout-all/
        """
        success = self.auth_service.logout_all_sessions(str(request.user.id))
        
        if success:
            return Response({'message': 'All sessions logged out successfully'})
        else:
            return Response(
                {'error': 'Logout all failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def password_reset(self, request):
        """
        Request password reset
        
        POST /auth/password-reset/
        Body: {"email": "user@example.com"}
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reset_request = PasswordResetRequest(
            email=serializer.validated_data['email']
        )
        
        # Always return success to prevent email enumeration
        self.auth_service.reset_password(reset_request)
        
        return Response({
            'message': 'If the email exists, a password reset link has been sent'
        })
    
    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request):
        """
        Confirm password reset
        
        POST /auth/password-reset-confirm/
        Body: {
            "token": "reset_token",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reset_request = PasswordResetRequest(
            email="",  # Not needed for confirmation
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password']
        )
        
        success = self.auth_service.reset_password(reset_request)
        
        if success:
            return Response({'message': 'Password reset successfully'})
        else:
            return Response(
                {'error': 'Invalid or expired reset token'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change user password
        
        POST /auth/change-password/
        Body: {
            "old_password": "oldpassword",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }
        """
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success = self.auth_service.change_password(
            str(request.user.id),
            serializer.validated_data['old_password'],
            serializer.validated_data['new_password']
        )
        
        if success:
            return Response({'message': 'Password changed successfully'})
        else:
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        """
        Refresh access token
        
        POST /auth/refresh-token/
        Body: {"refresh": "refresh_token"}
        """
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Implement token refresh logic
        # This would use your token service
        
        return Response({
            'access_token': 'new_access_token',
            'expires_in': 3600
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Get user profile
        
        GET /auth/profile/
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update user profile
        
        PATCH /auth/profile/
        Body: {
            "first_name": "John",
            "last_name": "Doe",
            "email": "newemail@example.com"
        }
        """
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def sessions(self, request):
        """
        Get user active sessions
        
        GET /auth/sessions/
        """
        # This would get sessions from the repository
        sessions_data = []  # self.auth_service.get_user_sessions(str(request.user.id))
        
        serializer = UserSessionSerializer(sessions_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def revoke_session(self, request):
        """
        Revoke specific session
        
        DELETE /auth/sessions/{session_id}/
        """
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'session_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = self.auth_service.logout(session_id)
        
        if success:
            return Response({'message': 'Session revoked successfully'})
        else:
            return Response(
                {'error': 'Failed to revoke session'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def security_events(self, request):
        """
        Get user security events
        
        GET /auth/security-events/
        """
        # This would get events from the repository
        events_data = []  # self.auth_service.get_security_events(str(request.user.id))
        
        serializer = SecurityEventSerializer(events_data, many=True)
        return Response(serializer.data)


class TwoFactorViewSet(GenericViewSet):
    """
    ViewSet for two-factor authentication operations
    """
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = None  # AuthenticationApplicationService()
    
    @action(detail=False, methods=['post'])
    def setup(self, request):
        """
        Setup two-factor authentication
        
        POST /auth/2fa/setup/
        """
        setup_data = self.auth_service.setup_two_factor(str(request.user.id))
        
        serializer = TwoFactorSetupSerializer(setup_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def enable(self, request):
        """
        Enable two-factor authentication
        
        POST /auth/2fa/enable/
        Body: {"totp_code": "123456"}
        """
        serializer = TwoFactorEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success = self.auth_service.enable_two_factor(
            str(request.user.id),
            serializer.validated_data['totp_code']
        )
        
        if success:
            return Response({'message': 'Two-factor authentication enabled'})
        else:
            return Response(
                {'error': 'Invalid TOTP code'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def disable(self, request):
        """
        Disable two-factor authentication
        
        POST /auth/2fa/disable/
        Body: {"password": "userpassword"}
        """
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success = self.auth_service.disable_two_factor(
            str(request.user.id),
            serializer.validated_data['password']
        )
        
        if success:
            return Response({'message': 'Two-factor authentication disabled'})
        else:
            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get two-factor authentication status
        
        GET /auth/2fa/status/
        """
        # Check if user has 2FA enabled
        has_2fa = hasattr(request.user, 'two_factor') and request.user.two_factor.is_enabled
        
        return Response({
            'enabled': has_2fa,
            'backup_codes_count': 0  # Would get from user's 2FA setup
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for authentication service
    
    GET /auth/health/
    """
    return Response({
        'status': 'healthy',
        'service': 'authentication',
        'timestamp': '2024-01-01T00:00:00Z'  # Would use actual timestamp
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@method_decorator(csrf_exempt)
def webhook_handler(request):
    """
    Webhook handler for external authentication providers
    
    POST /auth/webhook/
    """
    # Handle webhooks from OAuth providers, etc.
    return Response({'status': 'received'})
