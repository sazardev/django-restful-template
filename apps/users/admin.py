"""
User Django Admin Configuration.
Configuración personalizada del panel de administración para usuarios.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.users.infrastructure.models import User, UserProfile, UserGroup, UserGroupMembership


class CustomUserCreationForm(UserCreationForm):
    """Formulario personalizado para crear usuarios."""
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'role')


class CustomUserChangeForm(UserChangeForm):
    """Formulario personalizado para editar usuarios."""
    
    class Meta:
        model = User
        fields = '__all__'


class UserProfileInline(admin.StackedInline):
    """Inline para el perfil de usuario."""
    
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Perfil')
    fields = (
        ('date_of_birth', 'gender'),
        ('company', 'position'),
        ('language', 'timezone'),
        ('email_notifications', 'push_notifications', 'sms_notifications'),
        ('last_activity', 'ip_address'),
    )
    readonly_fields = ('last_activity', 'ip_address')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administración personalizada de usuarios."""
    
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    # Campos para mostrar en la lista
    list_display = (
        'email', 'username', 'get_full_name', 'role', 'status',
        'is_email_verified', 'is_active', 'created_at'
    )
    
    # Campos para filtrar
    list_filter = (
        'role', 'status', 'is_email_verified', 'is_active',
        'created_at', 'last_login'
    )
    
    # Campos de búsqueda
    search_fields = (
        'email', 'username', 'first_name', 'last_name', 'phone'
    )
    
    # Ordenamiento por defecto
    ordering = ('-created_at',)
    
    # Filtro por fecha
    date_hierarchy = 'created_at'
    
    # Campos de solo lectura
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'last_login',
        'get_full_name', 'get_avatar_preview'
    )
    
    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        (_('Información Personal'), {
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'phone', 'address', 'city', 'country'
            )
        }),
        (_('Avatar'), {
            'fields': ('avatar', 'get_avatar_preview'),
            'classes': ('collapse',)
        }),
        (_('Roles y Permisos'), {
            'fields': (
                'role', 'status', 'is_email_verified', 'is_active',
                'is_staff', 'is_superuser', 'groups', 'user_permissions'
            )
        }),
        (_('Fechas Importantes'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuración para agregar usuario
    add_fieldsets = (
        (_('Información Básica'), {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'password1', 'password2',
                'first_name', 'last_name', 'role'
            ),
        }),
        (_('Información Adicional'), {
            'classes': ('wide', 'collapse'),
            'fields': ('phone', 'address', 'city', 'country'),
        }),
    )
    
    # Inlines
    inlines = [UserProfileInline]
    
    # Acciones personalizadas
    actions = [
        'activate_users',
        'deactivate_users',
        'verify_email',
        'send_welcome_email'
    ]
    
    def get_full_name(self, obj):
        """Mostrar nombre completo."""
        return obj.get_full_name()
    get_full_name.short_description = _('Nombre Completo')
    
    def get_avatar_preview(self, obj):
        """Mostrar preview del avatar."""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover;" />',
                obj.avatar.url
            )
        return _('Sin avatar')
    get_avatar_preview.short_description = _('Preview Avatar')
    
    def activate_users(self, request, queryset):
        """Activar usuarios seleccionados."""
        updated = queryset.update(status='active', is_active=True)
        self.message_user(
            request,
            f'{updated} usuarios activados correctamente.'
        )
    activate_users.short_description = _('Activar usuarios seleccionados')
    
    def deactivate_users(self, request, queryset):
        """Desactivar usuarios seleccionados."""
        updated = queryset.update(status='inactive', is_active=False)
        self.message_user(
            request,
            f'{updated} usuarios desactivados correctamente.'
        )
    deactivate_users.short_description = _('Desactivar usuarios seleccionados')
    
    def verify_email(self, request, queryset):
        """Verificar email de usuarios seleccionados."""
        updated = queryset.update(is_email_verified=True)
        self.message_user(
            request,
            f'{updated} emails verificados correctamente.'
        )
    verify_email.short_description = _('Verificar email de usuarios seleccionados')
    
    def send_welcome_email(self, request, queryset):
        """Enviar email de bienvenida."""
        from apps.users.infrastructure.tasks import send_welcome_email_task
        
        count = 0
        for user in queryset:
            if user.is_email_verified:
                send_welcome_email_task.delay(user.email, user.get_full_name())
                count += 1
        
        self.message_user(
            request,
            f'Emails de bienvenida enviados a {count} usuarios.'
        )
    send_welcome_email.short_description = _('Enviar email de bienvenida')


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    """Administración de grupos de usuarios."""
    
    list_display = ('name', 'description', 'get_users_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('id', 'created_at', 'created_by')
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('name', 'description', 'is_active')
        }),
        (_('Permisos'), {
            'fields': ('permissions',)
        }),
        (_('Metadatos'), {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_users_count(self, obj):
        """Obtener cantidad de usuarios en el grupo."""
        return obj.users.count()
    get_users_count.short_description = _('Cantidad de Usuarios')
    
    def save_model(self, request, obj, form, change):
        """Guardar modelo estableciendo el creador."""
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserGroupMembership)
class UserGroupMembershipAdmin(admin.ModelAdmin):
    """Administración de membresías de grupos."""
    
    list_display = ('user', 'group', 'is_admin', 'joined_at', 'added_by')
    list_filter = ('is_admin', 'joined_at', 'group', 'added_by')
    search_fields = ('user__email', 'user__username', 'group__name')
    readonly_fields = ('id', 'joined_at')
    autocomplete_fields = ('user', 'group', 'added_by')
    
    def save_model(self, request, obj, form, change):
        """Guardar modelo estableciendo quien lo agregó."""
        if not change:  # Si es nuevo
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Administración de perfiles de usuario."""
    
    list_display = (
        'user', 'company', 'position', 'language',
        'email_notifications', 'last_activity'
    )
    list_filter = (
        'gender', 'language', 'timezone', 'email_notifications',
        'push_notifications', 'sms_notifications'
    )
    search_fields = ('user__email', 'user__username', 'company', 'position')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_activity', 'ip_address')
    autocomplete_fields = ('user',)
    
    fieldsets = (
        (_('Usuario'), {
            'fields': ('user',)
        }),
        (_('Información Personal'), {
            'fields': ('date_of_birth', 'gender')
        }),
        (_('Información Profesional'), {
            'fields': ('company', 'position')
        }),
        (_('Preferencias'), {
            'fields': ('language', 'timezone')
        }),
        (_('Notificaciones'), {
            'fields': (
                'email_notifications', 'push_notifications', 'sms_notifications'
            )
        }),
        (_('Metadatos'), {
            'fields': (
                'last_activity', 'ip_address', 'user_agent',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )


# Personalización del sitio de administración
admin.site.site_header = _('Logistics API - Administración')
admin.site.site_title = _('Logistics API Admin')
admin.site.index_title = _('Panel de Administración')

# Configuración adicional para mejor UX
admin.site.enable_nav_sidebar = True
