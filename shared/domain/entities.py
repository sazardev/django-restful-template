"""
Shared Domain Entities.
Entidades base y abstracciones compartidas entre dominios.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class Entity(ABC):
    """Entidad base del dominio."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if not self.id:
            self.id = uuid4()
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()
    
    def mark_as_updated(self):
        """Marcar entidad como actualizada."""
        self.updated_at = datetime.now()


@dataclass(frozen=True)
class ValueObject(ABC):
    """Objeto de valor base."""
    pass


@dataclass
class AggregateRoot(Entity):
    """Raíz de agregado base."""
    
    version: int = 1
    
    def increment_version(self):
        """Incrementar versión para control de concurrencia."""
        self.version += 1
        self.mark_as_updated()


@dataclass
class DomainEvent:
    """Evento de dominio base."""
    
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    event_data: Dict[str, Any]
    occurred_at: datetime
    version: int
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = uuid4()
        if not self.occurred_at:
            self.occurred_at = datetime.now()


class Repository(ABC):
    """Interface base para repositorios."""
    
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[Entity]:
        """Obtener entidad por ID."""
        pass
    
    @abstractmethod
    async def save(self, entity: Entity) -> Entity:
        """Guardar entidad."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Eliminar entidad."""
        pass


class EventBus(ABC):
    """Interface para el bus de eventos."""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publicar evento."""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler) -> None:
        """Suscribirse a evento."""
        pass


class UnitOfWork(ABC):
    """Interface para Unit of Work pattern."""
    
    @abstractmethod
    async def __aenter__(self):
        """Iniciar transacción."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finalizar transacción."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Confirmar cambios."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Revertir cambios."""
        pass
