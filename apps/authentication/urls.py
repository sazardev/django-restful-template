"""
Authentication URL Configuration
RESTful API endpoints for authentication and user management
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .presentation.views import (
    AuthenticationViewSet,
    TwoFactorViewSet,
    health_check,
    webhook_handler
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'auth', AuthenticationViewSet, basename='auth')
router.register(r'auth/2fa', TwoFactorViewSet, basename='2fa')

app_name = 'authentication'

urlpatterns = [
    # API RESTful endpoints
    path('api/v1/', include(router.urls)),
    
    # Health check
    path('api/v1/auth/health/', health_check, name='health-check'),
    
    # Webhook handler
    path('api/v1/auth/webhook/', webhook_handler, name='webhook'),
    
    # Authentication endpoints (handled by AuthenticationViewSet):
    # POST /api/v1/auth/login/               - User login
    # POST /api/v1/auth/register/            - User registration
    # POST /api/v1/auth/logout/              - User logout
    # POST /api/v1/auth/logout-all/          - Logout all sessions
    # POST /api/v1/auth/password-reset/      - Request password reset
    # POST /api/v1/auth/password-reset-confirm/ - Confirm password reset
    # POST /api/v1/auth/change-password/     - Change password
    # POST /api/v1/auth/refresh-token/       - Refresh access token
    # GET  /api/v1/auth/profile/             - Get user profile
    # PATCH /api/v1/auth/profile/            - Update user profile
    # GET  /api/v1/auth/sessions/            - Get user sessions
    # DELETE /api/v1/auth/sessions/          - Revoke session
    # GET  /api/v1/auth/security-events/     - Get security events
    
    # Two-Factor Authentication endpoints (handled by TwoFactorViewSet):
    # POST /api/v1/auth/2fa/setup/           - Setup 2FA
    # POST /api/v1/auth/2fa/enable/          - Enable 2FA
    # POST /api/v1/auth/2fa/disable/         - Disable 2FA
    # GET  /api/v1/auth/2fa/status/          - Get 2FA status
]
