"""
User Application Services.
Casos de uso para el sistema de usuarios.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from apps.users.domain.entities import UserEntity, UserProfile, UserStatus
from apps.users.domain.interfaces import (
    UserRepositoryInterface,
    EmailServiceInterface,
    PasswordServiceInterface,
    UserEventPublisherInterface
)
from apps.users.domain.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidPasswordException,
    UserNotActiveException,
    EmailNotVerifiedException,
    InsufficientPermissionsException
)
from apps.users.application.dtos import (
    CreateUserCommand,
    UpdateUserCommand,
    ChangeUserRoleCommand,
    ChangeUserStatusCommand,
    UserQuery,
    UserDTO,
    LoginCommand,
    LoginResponse,
    PasswordResetCommand,
    ConfirmPasswordResetCommand,
    ChangePasswordCommand,
    VerifyEmailCommand
)


class UserService:
    """Servicio de aplicación para usuarios."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        email_service: EmailServiceInterface,
        password_service: PasswordServiceInterface,
        event_publisher: UserEventPublisherInterface
    ):
        self.user_repository = user_repository
        self.email_service = email_service
        self.password_service = password_service
        self.event_publisher = event_publisher
    
    async def create_user(self, command: CreateUserCommand) -> UserDTO:
        """Crear un nuevo usuario."""
        # Verificar que el email no existe
        existing_user = await self.user_repository.get_by_email(command.email)
        if existing_user:
            raise UserAlreadyExistsException("email", command.email)
        
        # Verificar que el username no existe
        existing_username = await self.user_repository.get_by_username(command.username)
        if existing_username:
            raise UserAlreadyExistsException("username", command.username)
        
        # Crear perfil de usuario
        profile = UserProfile(
            first_name=command.first_name,
            last_name=command.last_name,
            phone=command.phone,
            address=command.address,
            city=command.city,
            country=command.country
        )
        
        # Crear entidad de usuario
        user = UserEntity(
            id=uuid4(),
            email=command.email,
            username=command.username,
            profile=profile,
            role=command.role,
            status=UserStatus.PENDING_VERIFICATION,
            is_email_verified=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Hashear contraseña
        hashed_password = self.password_service.hash_password(command.password)
        
        # Guardar usuario
        created_user = await self.user_repository.create(user)
        
        # Enviar email de verificación
        verification_token = self.password_service.generate_reset_token(user.email)
        await self.email_service.send_verification_email(user.email, verification_token)
        
        # Publicar evento
        await self.event_publisher.publish_user_created(created_user)
        
        return self._entity_to_dto(created_user)
    
    async def get_user_by_id(self, user_id: UUID) -> UserDTO:
        """Obtener usuario por ID."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        return self._entity_to_dto(user)
    
    async def update_user(self, command: UpdateUserCommand) -> UserDTO:
        """Actualizar usuario."""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundException(str(command.user_id))
        
        # Actualizar perfil
        updated_profile = UserProfile(
            first_name=command.first_name or user.profile.first_name,
            last_name=command.last_name or user.profile.last_name,
            phone=command.phone or user.profile.phone,
            address=command.address or user.profile.address,
            city=command.city or user.profile.city,
            country=command.country or user.profile.country,
            avatar=command.avatar or user.profile.avatar
        )
        
        user.profile = updated_profile
        user.updated_at = datetime.now()
        
        # Guardar cambios
        updated_user = await self.user_repository.update(user)
        
        # Publicar evento
        await self.event_publisher.publish_user_updated(updated_user)
        
        return self._entity_to_dto(updated_user)
    
    async def change_user_role(self, command: ChangeUserRoleCommand) -> UserDTO:
        """Cambiar rol de usuario."""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundException(str(command.user_id))
        
        # Verificar permisos del usuario que realiza el cambio
        performer = await self.user_repository.get_by_id(command.performed_by)
        if not performer or not performer.can_access_resource('manage_users'):
            raise InsufficientPermissionsException(
                str(command.performed_by), 'manage_users'
            )
        
        user.role = command.new_role
        user.updated_at = datetime.now()
        
        updated_user = await self.user_repository.update(user)
        await self.event_publisher.publish_user_updated(updated_user)
        
        return self._entity_to_dto(updated_user)
    
    async def change_user_status(self, command: ChangeUserStatusCommand) -> UserDTO:
        """Cambiar estado de usuario."""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundException(str(command.user_id))
        
        user.status = command.new_status
        user.updated_at = datetime.now()
        
        updated_user = await self.user_repository.update(user)
        await self.event_publisher.publish_user_updated(updated_user)
        
        return self._entity_to_dto(updated_user)
    
    async def list_users(self, query: UserQuery) -> List[UserDTO]:
        """Listar usuarios con filtros."""
        filters = {}
        if query.email:
            filters['email'] = query.email
        if query.username:
            filters['username'] = query.username
        if query.role:
            filters['role'] = query.role
        if query.status:
            filters['status'] = query.status
        if query.search:
            filters['search'] = query.search
        
        users = await self.user_repository.list_users(
            limit=query.limit,
            offset=query.offset,
            filters=filters
        )
        
        return [self._entity_to_dto(user) for user in users]
    
    async def delete_user(self, user_id: UUID, performed_by: UUID) -> bool:
        """Eliminar usuario."""
        # Verificar que el usuario existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        # Verificar permisos
        performer = await self.user_repository.get_by_id(performed_by)
        if not performer or not performer.can_access_resource('delete_users'):
            raise InsufficientPermissionsException(
                str(performed_by), 'delete_users'
            )
        
        # Eliminar usuario
        result = await self.user_repository.delete(user_id)
        if result:
            await self.event_publisher.publish_user_deleted(user_id)
        
        return result
    
    async def verify_email(self, command: VerifyEmailCommand) -> bool:
        """Verificar email de usuario."""
        email = self.password_service.verify_reset_token(command.token)
        if not email:
            return False
        
        user = await self.user_repository.get_by_email(email)
        if not user:
            return False
        
        user.verify_email()
        if user.status == UserStatus.PENDING_VERIFICATION:
            user.status = UserStatus.ACTIVE
        
        await self.user_repository.update(user)
        await self.email_service.send_welcome_email(user.email, user.profile.full_name)
        
        return True
    
    def _entity_to_dto(self, user: UserEntity) -> UserDTO:
        """Convertir entidad a DTO."""
        return UserDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            full_name=user.profile.full_name,
            role=user.role,
            status=user.status,
            phone=user.profile.phone,
            address=user.profile.address,
            city=user.profile.city,
            country=user.profile.country,
            avatar=user.profile.avatar,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            groups=user.groups,
            permissions=user.permissions
        )


class AuthenticationService:
    """Servicio de autenticación."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordServiceInterface,
        event_publisher: UserEventPublisherInterface
    ):
        self.user_repository = user_repository
        self.password_service = password_service
        self.event_publisher = event_publisher
    
    async def login(self, command: LoginCommand) -> LoginResponse:
        """Autenticar usuario."""
        # Buscar usuario por email o username
        if "@" in command.email_or_username:
            user = await self.user_repository.get_by_email(command.email_or_username)
        else:
            user = await self.user_repository.get_by_username(command.email_or_username)
        
        if not user:
            raise UserNotFoundException(command.email_or_username)
        
        # Verificar contraseña
        if not self.password_service.verify_password(command.password, user.password):
            raise InvalidPasswordException()
        
        # Verificar que el usuario esté activo
        if not user.is_active_user():
            if not user.is_email_verified:
                raise EmailNotVerifiedException(user.email)
            else:
                raise UserNotActiveException(str(user.id))
        
        # Actualizar último login
        user.last_login = datetime.now()
        await self.user_repository.update(user)
        
        # Publicar evento de login
        await self.event_publisher.publish_user_logged_in(user)
        
        # Generar tokens (esto se implementaría con JWT)
        access_token = "access_token_placeholder"
        refresh_token = "refresh_token_placeholder"
        
        return LoginResponse(
            user=self._entity_to_dto(user),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600
        )
    
    async def request_password_reset(self, command: PasswordResetCommand) -> bool:
        """Solicitar reset de contraseña."""
        user = await self.user_repository.get_by_email(command.email)
        if not user:
            # Por seguridad, no revelamos si el email existe
            return True
        
        reset_token = self.password_service.generate_reset_token(user.email)
        await self.email_service.send_password_reset_email(user.email, reset_token)
        
        return True
    
    async def confirm_password_reset(self, command: ConfirmPasswordResetCommand) -> bool:
        """Confirmar reset de contraseña."""
        email = self.password_service.verify_reset_token(command.token)
        if not email:
            return False
        
        user = await self.user_repository.get_by_email(email)
        if not user:
            return False
        
        # Hashear nueva contraseña
        hashed_password = self.password_service.hash_password(command.new_password)
        
        # Actualizar usuario (esto requeriría un campo password en la entidad)
        user.updated_at = datetime.now()
        await self.user_repository.update(user)
        
        return True
    
    async def change_password(self, command: ChangePasswordCommand) -> bool:
        """Cambiar contraseña."""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundException(str(command.user_id))
        
        # Verificar contraseña actual
        if not self.password_service.verify_password(command.current_password, user.password):
            raise InvalidPasswordException("Contraseña actual incorrecta")
        
        # Hashear nueva contraseña
        hashed_password = self.password_service.hash_password(command.new_password)
        
        # Actualizar usuario
        user.updated_at = datetime.now()
        await self.user_repository.update(user)
        
        return True
    
    def _entity_to_dto(self, user: UserEntity) -> UserDTO:
        """Convertir entidad a DTO."""
        return UserDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            full_name=user.profile.full_name,
            role=user.role,
            status=user.status,
            phone=user.profile.phone,
            address=user.profile.address,
            city=user.profile.city,
            country=user.profile.country,
            avatar=user.profile.avatar,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            groups=user.groups,
            permissions=user.permissions
        )
