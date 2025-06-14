"""
User API Serializers.
Serializadores para la API REST de usuarios.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.users.domain.entities import UserRole, UserStatus
from apps.users.infrastructure.models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializador para el perfil de usuario."""
    
    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth', 'gender', 'company', 'position',
            'language', 'timezone', 'email_notifications',
            'push_notifications', 'sms_notifications'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear usuarios."""
    
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    role = serializers.ChoiceField(
        choices=[role.value for role in UserRole],
        default=UserRole.CLIENT.value
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'address',
            'city', 'country', 'role'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                "Las contraseñas no coinciden."
            )
        return attrs
    
    def validate_email(self, value):
        """Validar que el email sea único."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario con este email."
            )
        return value
    
    def validate_username(self, value):
        """Validar que el username sea único."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario con este username."
            )
        return value
    
    def create(self, validated_data):
        """Crear usuario con contraseña hasheada."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializador para actualizar usuarios."""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'address',
            'city', 'country', 'avatar'
        ]


class UserListSerializer(serializers.ModelSerializer):
    """Serializador para listar usuarios."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'role', 'role_display', 'status', 'status_display',
            'is_email_verified', 'created_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado de usuario."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    profile = UserProfileSerializer(read_only=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone', 'address', 'city', 'country',
            'avatar', 'role', 'role_display', 'status', 'status_display',
            'is_email_verified', 'is_active', 'created_at', 'updated_at',
            'last_login', 'profile', 'groups', 'permissions'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_login',
            'is_email_verified', 'groups', 'permissions'
        ]
    
    def get_permissions(self, obj):
        """Obtener permisos del usuario."""
        permissions = []
        
        # Permisos directos del usuario
        user_permissions = obj.user_permissions.all()
        permissions.extend([perm.codename for perm in user_permissions])
        
        # Permisos de grupos
        for group in obj.groups.all():
            group_permissions = group.permissions.all()
            permissions.extend([perm.codename for perm in group_permissions])
        
        return list(set(permissions))  # Eliminar duplicados


class ChangePasswordSerializer(serializers.Serializer):
    """Serializador para cambio de contraseña."""
    
    current_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validar que las nuevas contraseñas coincidan."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                "Las nuevas contraseñas no coinciden."
            )
        return attrs
    
    def validate_current_password(self, value):
        """Validar la contraseña actual."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "La contraseña actual es incorrecta."
            )
        return value


class PasswordResetSerializer(serializers.Serializer):
    """Serializador para solicitar reset de contraseña."""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validar que el email exista."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No existe un usuario con este email."
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializador para confirmar reset de contraseña."""
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                "Las contraseñas no coinciden."
            )
        return attrs


class ChangeUserRoleSerializer(serializers.Serializer):
    """Serializador para cambiar rol de usuario."""
    
    role = serializers.ChoiceField(
        choices=[role.value for role in UserRole],
        required=True
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )


class ChangeUserStatusSerializer(serializers.Serializer):
    """Serializador para cambiar estado de usuario."""
    
    status = serializers.ChoiceField(
        choices=[status.value for status in UserStatus],
        required=True
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )
