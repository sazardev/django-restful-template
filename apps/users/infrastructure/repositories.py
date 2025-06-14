"""
User Repository Implementation.
Implementación del repositorio de usuarios usando Django ORM.
"""

from typing import List, Optional
from uuid import UUID
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from apps.users.domain.entities import UserEntity, UserProfile, UserRole, UserStatus
from apps.users.domain.interfaces import UserRepositoryInterface
from apps.users.infrastructure.models import User


class DjangoUserRepository(UserRepositoryInterface):
    """Implementación del repositorio de usuarios con Django ORM."""
    
    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Obtener usuario por ID."""
        try:
            user = await User.objects.select_related('profile').aget(id=user_id)
            return self._model_to_entity(user)
        except ObjectDoesNotExist:
            return None
    
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Obtener usuario por email."""
        try:
            user = await User.objects.select_related('profile').aget(email=email)
            return self._model_to_entity(user)
        except ObjectDoesNotExist:
            return None
    
    async def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Obtener usuario por username."""
        try:
            user = await User.objects.select_related('profile').aget(username=username)
            return self._model_to_entity(user)
        except ObjectDoesNotExist:
            return None
    
    async def create(self, user: UserEntity) -> UserEntity:
        """Crear un nuevo usuario."""
        django_user = User(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            phone=user.profile.phone,
            address=user.profile.address,
            city=user.profile.city,
            country=user.profile.country,
            avatar=user.profile.avatar,
            role=user.role.value,
            status=user.status.value,
            is_email_verified=user.is_email_verified,
        )
        
        await django_user.asave()
        return self._model_to_entity(django_user)
    
    async def update(self, user: UserEntity) -> UserEntity:
        """Actualizar usuario existente."""
        try:
            django_user = await User.objects.aget(id=user.id)
            
            # Actualizar campos
            django_user.email = user.email
            django_user.username = user.username
            django_user.first_name = user.profile.first_name
            django_user.last_name = user.profile.last_name
            django_user.phone = user.profile.phone
            django_user.address = user.profile.address
            django_user.city = user.profile.city
            django_user.country = user.profile.country
            django_user.avatar = user.profile.avatar
            django_user.role = user.role.value
            django_user.status = user.status.value
            django_user.is_email_verified = user.is_email_verified
            django_user.last_login = user.last_login
            
            await django_user.asave()
            return self._model_to_entity(django_user)
        except ObjectDoesNotExist:
            raise ValueError(f"Usuario con ID {user.id} no encontrado")
    
    async def delete(self, user_id: UUID) -> bool:
        """Eliminar usuario."""
        try:
            user = await User.objects.aget(id=user_id)
            await user.adelete()
            return True
        except ObjectDoesNotExist:
            return False
    
    async def list_users(
        self, 
        limit: int = 20, 
        offset: int = 0,
        filters: Optional[dict] = None
    ) -> List[UserEntity]:
        """Listar usuarios con filtros."""
        queryset = User.objects.select_related('profile').all()
        
        if filters:
            if 'email' in filters:
                queryset = queryset.filter(email__icontains=filters['email'])
            
            if 'username' in filters:
                queryset = queryset.filter(username__icontains=filters['username'])
            
            if 'role' in filters:
                queryset = queryset.filter(role=filters['role'].value)
            
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'].value)
            
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(username__icontains=search_term)
                )
        
        queryset = queryset.order_by('-created_at')[offset:offset + limit]
        users = [user async for user in queryset]
        
        return [self._model_to_entity(user) for user in users]
    
    async def count(self, filters: Optional[dict] = None) -> int:
        """Contar usuarios."""
        queryset = User.objects.all()
        
        if filters:
            if 'email' in filters:
                queryset = queryset.filter(email__icontains=filters['email'])
            
            if 'username' in filters:
                queryset = queryset.filter(username__icontains=filters['username'])
            
            if 'role' in filters:
                queryset = queryset.filter(role=filters['role'].value)
            
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'].value)
            
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(username__icontains=search_term)
                )
        
        return await queryset.acount()
    
    def _model_to_entity(self, user: User) -> UserEntity:
        """Convertir modelo Django a entidad de dominio."""
        profile = UserProfile(
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            address=user.address,
            city=user.city,
            country=user.country,
            avatar=user.avatar.url if user.avatar else None
        )
        
        # Obtener grupos y permisos
        groups = []
        permissions = []
        
        # En una implementación real, aquí cargaríamos los grupos y permisos
        # groups = [group.name for group in user.groups.all()]
        # permissions = [perm.codename for perm in user.user_permissions.all()]
        
        return UserEntity(
            id=user.id,
            email=user.email,
            username=user.username,
            profile=profile,
            role=UserRole(user.role),
            status=UserStatus(user.status),
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            groups=groups,
            permissions=permissions
        )
