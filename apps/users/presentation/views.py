"""
User API Views.
Vistas para la API REST de usuarios con inyección de dependencias.
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.contrib.auth import get_user_model

from apps.users.infrastructure.models import User
from apps.users.presentation.serializers import (
    UserCreateSerializer,
    UserUpdateSerializer,
    UserListSerializer,
    UserDetailSerializer,
    ChangePasswordSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    ChangeUserRoleSerializer,
    ChangeUserStatusSerializer
)
from apps.users.application.services import UserService, AuthenticationService
from apps.users.application.dtos import (
    CreateUserCommand,
    UpdateUserCommand,
    ChangeUserRoleCommand,
    ChangeUserStatusCommand,
    UserQuery,
    ChangePasswordCommand,
    PasswordResetCommand,
    ConfirmPasswordResetCommand
)
from apps.users.domain.entities import UserRole, UserStatus
from shared.infrastructure.permissions import IsOwnerOrAdminPermission
from shared.infrastructure.pagination import StandardResultsSetPagination
from shared.infrastructure.exceptions import ValidationError, NotFoundError


User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        description="Obtener lista paginada de usuarios con filtros opcionales.",
        tags=["Usuarios"]
    ),
    create=extend_schema(
        summary="Crear usuario",
        description="Crear un nuevo usuario en el sistema.",
        tags=["Usuarios"]
    ),
    retrieve=extend_schema(
        summary="Obtener usuario",
        description="Obtener detalles de un usuario específico.",
        tags=["Usuarios"]
    ),
    update=extend_schema(
        summary="Actualizar usuario",
        description="Actualizar información de un usuario.",
        tags=["Usuarios"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente usuario",
        description="Actualizar parcialmente información de un usuario.",
        tags=["Usuarios"]
    ),
    destroy=extend_schema(
        summary="Eliminar usuario",
        description="Eliminar un usuario del sistema.",
        tags=["Usuarios"]
    )
)
class UserViewSet(ModelViewSet):
    """
    ViewSet para gestión de usuarios.
    Implementa CRUD completo con inyección de dependencias.
    """
    
    queryset = User.objects.select_related('profile').prefetch_related('groups')
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'status', 'is_email_verified', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['created_at', 'updated_at', 'last_login', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inyección de dependencias
        from apps.users.infrastructure.repositories import DjangoUserRepository
        from apps.users.infrastructure.services import (
            DjangoEmailService,
            DjangoPasswordService,
            CeleryUserEventPublisher
        )
        
        self.user_service = UserService(
            user_repository=DjangoUserRepository(),
            email_service=DjangoEmailService(),
            password_service=DjangoPasswordService(),
            event_publisher=CeleryUserEventPublisher()
        )
    
    def get_serializer_class(self):
        """Obtener serializador según la acción."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action == 'create':
            # Crear usuario puede ser público para registro
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Solo el propietario o admin puede modificar/eliminar
            permission_classes = [IsOwnerOrAdminPermission]
        else:
            # Otras acciones requieren autenticación
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    async def create(self, request):
        """Crear un nuevo usuario."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Convertir a comando de dominio
            command = CreateUserCommand(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                role=UserRole(serializer.validated_data.get('role', UserRole.CLIENT.value)),
                phone=serializer.validated_data.get('phone'),
                address=serializer.validated_data.get('address'),
                city=serializer.validated_data.get('city'),
                country=serializer.validated_data.get('country')
            )
            
            # Crear usuario usando el servicio de aplicación
            user_dto = await self.user_service.create_user(command)
            
            # Serializar respuesta
            response_serializer = UserDetailSerializer(user_dto)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def update(self, request, pk=None):
        """Actualizar usuario."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Convertir a comando de dominio
            command = UpdateUserCommand(
                user_id=pk,
                **serializer.validated_data
            )
            
            # Actualizar usando el servicio
            user_dto = await self.user_service.update_user(command)
            
            # Serializar respuesta
            response_serializer = UserDetailSerializer(user_dto)
            
            return Response(response_serializer.data)
        
        except NotFoundError:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def destroy(self, request, pk=None):
        """Eliminar usuario."""
        try:
            success = await self.user_service.delete_user(
                user_id=pk,
                performed_by=request.user.id
            )
            
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'error': 'No se pudo eliminar el usuario'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except NotFoundError:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Perfil del usuario actual",
        description="Obtener perfil del usuario autenticado.",
        tags=["Usuarios"]
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    async def me(self, request):
        """Obtener perfil del usuario actual."""
        try:
            user_dto = await self.user_service.get_user_by_id(request.user.id)
            serializer = UserDetailSerializer(user_dto)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': 'Error obteniendo perfil'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Cambiar contraseña",
        description="Cambiar la contraseña del usuario actual.",
        request=ChangePasswordSerializer,
        tags=["Usuarios"]
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    async def change_password(self, request):
        """Cambiar contraseña del usuario actual."""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            command = ChangePasswordCommand(
                user_id=request.user.id,
                current_password=serializer.validated_data['current_password'],
                new_password=serializer.validated_data['new_password']
            )
            
            # Usar servicio de autenticación
            from apps.users.infrastructure.repositories import DjangoUserRepository
            from apps.users.infrastructure.services import (
                DjangoPasswordService,
                CeleryUserEventPublisher
            )
            
            auth_service = AuthenticationService(
                user_repository=DjangoUserRepository(),
                password_service=DjangoPasswordService(),
                event_publisher=CeleryUserEventPublisher()
            )
            
            success = await auth_service.change_password(command)
            
            if success:
                return Response({'message': 'Contraseña cambiada exitosamente'})
            else:
                return Response(
                    {'error': 'No se pudo cambiar la contraseña'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': 'Error cambiando contraseña'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Cambiar rol de usuario",
        description="Cambiar el rol de un usuario (solo administradores).",
        request=ChangeUserRoleSerializer,
        tags=["Usuarios"]
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    async def change_role(self, request, pk=None):
        """Cambiar rol de usuario."""
        serializer = ChangeUserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            command = ChangeUserRoleCommand(
                user_id=pk,
                new_role=UserRole(serializer.validated_data['role']),
                performed_by=request.user.id
            )
            
            user_dto = await self.user_service.change_user_role(command)
            response_serializer = UserDetailSerializer(user_dto)
            
            return Response(response_serializer.data)
        
        except Exception as e:
            return Response(
                {'error': 'Error cambiando rol'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Cambiar estado de usuario",
        description="Cambiar el estado de un usuario (solo administradores).",
        request=ChangeUserStatusSerializer,
        tags=["Usuarios"]
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    async def change_status(self, request, pk=None):
        """Cambiar estado de usuario."""
        serializer = ChangeUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            command = ChangeUserStatusCommand(
                user_id=pk,
                new_status=UserStatus(serializer.validated_data['status']),
                reason=serializer.validated_data.get('reason'),
                performed_by=request.user.id
            )
            
            user_dto = await self.user_service.change_user_status(command)
            response_serializer = UserDetailSerializer(user_dto)
            
            return Response(response_serializer.data)
        
        except Exception as e:
            return Response(
                {'error': 'Error cambiando estado'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    summary="Solicitar reset de contraseña",
    description="Enviar email para restablecer contraseña.",
    request=PasswordResetSerializer,
    tags=["Autenticación"]
)
class PasswordResetView(APIView):
    """Vista para solicitar reset de contraseña."""
    
    permission_classes = [permissions.AllowAny]
    
    async def post(self, request):
        """Solicitar reset de contraseña."""
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Inyección de dependencias
            from apps.users.infrastructure.repositories import DjangoUserRepository
            from apps.users.infrastructure.services import (
                DjangoPasswordService,
                CeleryUserEventPublisher
            )
            
            auth_service = AuthenticationService(
                user_repository=DjangoUserRepository(),
                password_service=DjangoPasswordService(),
                event_publisher=CeleryUserEventPublisher()
            )
            
            command = PasswordResetCommand(
                email=serializer.validated_data['email']
            )
            
            await auth_service.request_password_reset(command)
            
            return Response({
                'message': 'Si el email existe, se ha enviado un enlace de reset.'
            })
        
        except Exception as e:
            return Response(
                {'error': 'Error procesando solicitud'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    summary="Confirmar reset de contraseña",
    description="Confirmar reset de contraseña con token.",
    request=PasswordResetConfirmSerializer,
    tags=["Autenticación"]
)
class PasswordResetConfirmView(APIView):
    """Vista para confirmar reset de contraseña."""
    
    permission_classes = [permissions.AllowAny]
    
    async def post(self, request):
        """Confirmar reset de contraseña."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Inyección de dependencias
            from apps.users.infrastructure.repositories import DjangoUserRepository
            from apps.users.infrastructure.services import (
                DjangoPasswordService,
                CeleryUserEventPublisher
            )
            
            auth_service = AuthenticationService(
                user_repository=DjangoUserRepository(),
                password_service=DjangoPasswordService(),
                event_publisher=CeleryUserEventPublisher()
            )
            
            command = ConfirmPasswordResetCommand(
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password']
            )
            
            success = await auth_service.confirm_password_reset(command)
            
            if success:
                return Response({
                    'message': 'Contraseña restablecida exitosamente.'
                })
            else:
                return Response(
                    {'error': 'Token inválido o expirado.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': 'Error restableciendo contraseña'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
