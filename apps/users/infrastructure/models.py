"""
User Django Models.
Modelos de Django para el sistema de usuarios.
"""

import uuid
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from apps.users.domain.entities import UserRole, UserStatus


class User(AbstractUser):
    """
    Modelo de usuario personalizado.
    Extiende AbstractUser de Django con campos adicionales.
    """
    
    # Campos únicos
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name=_('Email'),
        help_text=_('Email único del usuario')
    )
    
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=_('Username solo puede contener letras, números y @/./+/-/_')
            )
        ],
        verbose_name=_('Username'),
        help_text=_('Username único del usuario')
    )
    
    # Campos de perfil
    first_name = models.CharField(
        max_length=150,
        verbose_name=_('Nombre')
    )
    
    last_name = models.CharField(
        max_length=150,
        verbose_name=_('Apellido')
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Número de teléfono inválido')
            )
        ],
        verbose_name=_('Teléfono')
    )
    
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Dirección')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Ciudad')
    )
    
    country = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name=_('País'),
        help_text=_('Código de país ISO 3166-1 alpha-2')
    )
    
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name=_('Avatar')
    )
    
    # Campos de rol y estado
    role = models.CharField(
        max_length=20,
        choices=[(role.value, role.value.replace('_', ' ').title()) for role in UserRole],
        default=UserRole.CLIENT.value,
        verbose_name=_('Rol')
    )
    
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value.replace('_', ' ').title()) for status in UserStatus],
        default=UserStatus.PENDING_VERIFICATION.value,
        verbose_name=_('Estado')
    )
    
    # Campos de verificación
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name=_('Email verificado')
    )
    
    email_verification_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Token de verificación de email')
    )
      # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de actualización')
    )
    
    # Resolver conflictos con AbstractUser
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    
    # Configuración de Django
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        db_table = 'users_user'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retorna el primer nombre del usuario."""
        return self.first_name
    
    @property
    def is_active_user(self):
        """Verifica si el usuario está activo y verificado."""
        return (
            self.is_active and 
            self.status == UserStatus.ACTIVE.value and 
            self.is_email_verified
        )
    
    def can_access_resource(self, resource: str) -> bool:
        """Verifica si el usuario puede acceder a un recurso."""
        if self.role == UserRole.SUPER_ADMIN.value:
            return True
        
        role_permissions = {
            UserRole.LOGISTICS_MANAGER.value: [
                'view_logistics', 'manage_logistics', 'view_reports'
            ],
            UserRole.FLEET_MANAGER.value: [
                'view_vehicles', 'manage_vehicles', 'view_tracking'
            ],
            UserRole.AUCTION_MANAGER.value: [
                'view_auctions', 'manage_auctions', 'create_auctions'
            ],
            UserRole.DRIVER.value: [
                'view_own_vehicles', 'update_location'
            ],
            UserRole.CLIENT.value: [
                'view_auctions', 'place_bids', 'view_own_orders'
            ]
        }
        
        allowed_permissions = role_permissions.get(self.role, [])
        return resource in allowed_permissions


class UserGroup(models.Model):
    """
    Grupos de usuarios personalizados.
    Extiende la funcionalidad de grupos de Django.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Nombre')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    
    users = models.ManyToManyField(
        User,
        through='UserGroupMembership',
        through_fields=('group', 'user'),
        related_name='custom_groups',
        verbose_name=_('Usuarios')
    )
    
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name=_('Permisos')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        verbose_name=_('Creado por')
    )
    
    class Meta:
        verbose_name = _('Grupo de usuarios')
        verbose_name_plural = _('Grupos de usuarios')
        db_table = 'users_usergroup'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserGroupMembership(models.Model):
    """
    Membresía de usuarios en grupos.
    Tabla intermedia para relación many-to-many con campos adicionales.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Usuario')
    )
    
    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        verbose_name=_('Grupo')
    )
    
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de ingreso')
    )
    
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='group_memberships_added',
        verbose_name=_('Agregado por')
    )
    
    is_admin = models.BooleanField(
        default=False,
        verbose_name=_('Es administrador del grupo')
    )
    
    class Meta:
        verbose_name = _('Membresía de grupo')
        verbose_name_plural = _('Membresías de grupo')
        db_table = 'users_usergroupmembership'
        unique_together = ['user', 'group']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user} - {self.group}"


class UserProfile(models.Model):
    """
    Perfil extendido de usuario.
    Información adicional que no está en el modelo User.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Usuario')
    )
    
    # Información personal adicional
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Fecha de nacimiento')
    )
    
    gender = models.CharField(
        max_length=10,
        choices=[
            ('M', _('Masculino')),
            ('F', _('Femenino')),
            ('O', _('Otro')),
            ('N', _('Prefiero no decir'))
        ],
        blank=True,
        null=True,
        verbose_name=_('Género')
    )
    
    # Información profesional
    company = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Empresa')
    )
    
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Cargo')
    )
    
    # Preferencias
    language = models.CharField(
        max_length=10,
        choices=[
            ('es', _('Español')),
            ('en', _('Inglés')),
            ('fr', _('Francés')),
        ],
        default='es',
        verbose_name=_('Idioma')
    )
    
    timezone = models.CharField(
        max_length=50,
        default='America/Mexico_City',
        verbose_name=_('Zona horaria')
    )
    
    # Configuraciones de notificaciones
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Notificaciones por email')
    )
    
    push_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Notificaciones push')
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name=_('Notificaciones por SMS')
    )
    
    # Metadatos
    last_activity = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Última actividad')
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('Dirección IP')
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User Agent')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de actualización')
    )
    
    class Meta:
        verbose_name = _('Perfil de usuario')
        verbose_name_plural = _('Perfiles de usuario')
        db_table = 'users_userprofile'
    
    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"
