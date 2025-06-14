"""
Notification Presentation Views.
Vistas para la presentación de notificaciones.
"""

import logging
from typing import Dict, Any
from uuid import UUID
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.notifications.application.services import (
    NotificationApplicationService, NotificationBroadcastService
)
from apps.notifications.application.dtos import (
    CreateNotificationDTO, NotificationFilterDTO, BroadcastNotificationDTO
)
from apps.notifications.domain.entities import NotificationType, NotificationPriority
from apps.notifications.infrastructure.models import NotificationModel
from apps.notifications.presentation.serializers import (
    NotificationSerializer, NotificationCreateSerializer, NotificationListSerializer,
    NotificationFilterSerializer, MarkNotificationsSerializer, BroadcastNotificationSerializer,
    NotificationStatsSerializer, NotificationSummarySerializer
)
from shared.infrastructure.permissions import IsOwnerOrReadOnlyPermission
from shared.infrastructure.pagination import StandardPagination
from shared.domain.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet para notificaciones."""
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Obtener queryset filtrado por usuario."""
        return NotificationModel.objects.filter(
            user=self.request.user
        ).select_related('user', 'created_by')
    
    def get_serializer_class(self):
        """Obtener clase de serializador según la acción."""
        if self.action == 'create':
            return NotificationCreateSerializer
        elif self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'summary':
            return NotificationSummarySerializer
        return super().get_serializer_class()
    
    @extend_schema(
        summary="Listar notificaciones del usuario",
        description="Obtiene las notificaciones del usuario autenticado con filtros opcionales",
        parameters=[
            OpenApiParameter('unread_only', bool, description='Solo notificaciones no leídas'),
            OpenApiParameter('notification_type', str, description='Filtrar por tipo'),
            OpenApiParameter('priority', int, description='Filtrar por prioridad'),
        ]
    )
    def list(self, request: Request) -> Response:
        """Listar notificaciones del usuario con filtros."""
        try:
            # Obtener parámetros de filtro
            filter_serializer = NotificationFilterSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = NotificationApplicationService()
            
            # Aplicar filtros
            queryset = self.get_queryset()
            
            if filter_serializer.validated_data.get('unread_only'):
                queryset = queryset.filter(is_read=False)
            
            if filter_serializer.validated_data.get('notification_type'):
                queryset = queryset.filter(
                    notification_type=filter_serializer.validated_data['notification_type']
                )
            
            if filter_serializer.validated_data.get('priority'):
                queryset = queryset.filter(
                    priority=filter_serializer.validated_data['priority']
                )
            
            if filter_serializer.validated_data.get('date_from'):
                queryset = queryset.filter(
                    created_at__gte=filter_serializer.validated_data['date_from']
                )
            
            if filter_serializer.validated_data.get('date_to'):
                queryset = queryset.filter(
                    created_at__lte=filter_serializer.validated_data['date_to']
                )
            
            # Paginación
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = NotificationSerializer(page, many=True)
                
                # Agregar estadísticas
                unread_count = service.get_unread_count(request.user.id)
                
                response_data = {
                    'notifications': serializer.data,
                    'total_count': queryset.count(),
                    'unread_count': unread_count,
                    'has_next': self.paginator.page.has_next(),
                    'has_previous': self.paginator.page.has_previous(),
                }
                
                return self.get_paginated_response(response_data)
            
            serializer = NotificationSerializer(queryset, many=True)
            unread_count = service.get_unread_count(request.user.id)
            
            return Response({
                'notifications': serializer.data,
                'total_count': queryset.count(),
                'unread_count': unread_count,
                'has_next': False,
                'has_previous': False,
            })
        
        except Exception as e:
            logger.error(f"Error en list notifications: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Crear notificación",
        description="Crea una nueva notificación (solo para admins o sistema)",
    )
    def create(self, request: Request) -> Response:
        """Crear nueva notificación."""
        if not request.user.is_staff:
            return Response(
                {'error': 'No tienes permisos para crear notificaciones'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = NotificationApplicationService()
            
            notification = service.create_notification(
                user_id=serializer.validated_data['user_id'],
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                notification_type=NotificationType(serializer.validated_data['notification_type']),
                priority=NotificationPriority(serializer.validated_data['priority']),
                data=serializer.validated_data.get('data'),
                expires_in_hours=serializer.validated_data.get('expires_in_hours'),
                created_by_id=request.user.id,
                send_realtime=serializer.validated_data.get('send_realtime', True)
            )
            
            return Response(
                NotificationSerializer(notification).data,
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creando notificación: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Marcar notificación como leída",
        description="Marca una notificación específica como leída",
    )
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request: Request, pk=None) -> Response:
        """Marcar notificación como leída."""
        try:
            service = NotificationApplicationService()
            success = service.mark_as_read(UUID(pk), request.user.id)
            
            if success:
                unread_count = service.get_unread_count(request.user.id)
                return Response({
                    'success': True,
                    'unread_count': unread_count
                })
            else:
                return Response(
                    {'error': 'No se pudo marcar como leída'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error marcando como leída: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Marcar todas como leídas",
        description="Marca todas las notificaciones del usuario como leídas",
    )
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request: Request) -> Response:
        """Marcar todas las notificaciones como leídas."""
        try:
            service = NotificationApplicationService()
            count = service.mark_all_as_read(request.user.id)
            
            return Response({
                'success': True,
                'marked_count': count,
                'unread_count': 0
            })
        
        except Exception as e:
            logger.error(f"Error marcando todas como leídas: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Obtener contador de no leídas",
        description="Obtiene el número de notificaciones no leídas del usuario",
    )
    @action(detail=False, methods=['get'])
    def unread_count(self, request: Request) -> Response:
        """Obtener contador de notificaciones no leídas."""
        try:
            service = NotificationApplicationService()
            count = service.get_unread_count(request.user.id)
            
            return Response({'unread_count': count})
        
        except Exception as e:
            logger.error(f"Error obteniendo contador: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Obtener estadísticas",
        description="Obtiene estadísticas de notificaciones del usuario",
    )
    @method_decorator(cache_page(300))  # Cache por 5 minutos
    @action(detail=False, methods=['get'])
    def stats(self, request: Request) -> Response:
        """Obtener estadísticas de notificaciones."""
        try:
            queryset = self.get_queryset()
            
            total_notifications = queryset.count()
            unread_count = queryset.filter(is_read=False).count()
            read_count = total_notifications - unread_count
            
            # Notificaciones por tipo
            notifications_by_type = {}
            for notification_type in NotificationType:
                count = queryset.filter(notification_type=notification_type.value).count()
                notifications_by_type[notification_type.value] = count
            
            # Notificaciones por prioridad
            notifications_by_priority = {}
            for priority in NotificationPriority:
                count = queryset.filter(priority=priority.value).count()
                notifications_by_priority[str(priority.value)] = count
            
            # Notificaciones recientes (últimas 24 horas)
            from django.utils import timezone
            from datetime import timedelta
            
            recent_date = timezone.now() - timedelta(hours=24)
            recent_notifications_count = queryset.filter(created_at__gte=recent_date).count()
            
            stats_data = {
                'total_notifications': total_notifications,
                'unread_count': unread_count,
                'read_count': read_count,
                'notifications_by_type': notifications_by_type,
                'notifications_by_priority': notifications_by_priority,
                'recent_notifications_count': recent_notifications_count,
            }
            
            return Response(stats_data)
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Resumen de notificaciones",
        description="Obtiene un resumen compacto de las notificaciones recientes",
    )
    @action(detail=False, methods=['get'])
    def summary(self, request: Request) -> Response:
        """Obtener resumen de notificaciones recientes."""
        try:
            # Últimas 10 notificaciones no leídas
            recent_notifications = self.get_queryset().filter(
                is_read=False
            ).order_by('-created_at')[:10]
            
            serializer = NotificationSummarySerializer(recent_notifications, many=True)
            
            service = NotificationApplicationService()
            unread_count = service.get_unread_count(request.user.id)
            
            return Response({
                'recent_notifications': serializer.data,
                'unread_count': unread_count,
                'has_more': unread_count > 10
            })
        
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Limpiar notificaciones expiradas",
        description="Limpia las notificaciones expiradas (solo para admins)",
    )
    @action(detail=False, methods=['post'])
    def cleanup_expired(self, request: Request) -> Response:
        """Limpiar notificaciones expiradas."""
        if not request.user.is_staff:
            return Response(
                {'error': 'No tienes permisos para esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            service = NotificationApplicationService()
            count = service.cleanup_expired_notifications()
            
            return Response({
                'success': True,
                'cleaned_count': count
            })
        
        except Exception as e:
            logger.error(f"Error limpiando notificaciones expiradas: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationBroadcastViewSet(viewsets.ViewSet):
    """ViewSet para broadcast de notificaciones."""
    
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Solo staff puede hacer broadcast."""
        permissions = super().get_permissions()
        if not self.request.user.is_staff:
            from rest_framework.permissions import BasePermission
            
            class NoPermission(BasePermission):
                def has_permission(self, request, view):
                    return False
            
            permissions.append(NoPermission())
        return permissions
    
    @extend_schema(
        summary="Enviar broadcast a todos los usuarios",
        description="Envía una notificación a todos los usuarios activos",
    )
    @action(detail=False, methods=['post'])
    def broadcast_all(self, request: Request) -> Response:
        """Enviar broadcast a todos los usuarios."""
        serializer = BroadcastNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = NotificationBroadcastService()
            
            count = service.broadcast_to_all_users(
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                notification_type=NotificationType(serializer.validated_data['notification_type']),
                priority=NotificationPriority(serializer.validated_data['priority']),
                data=serializer.validated_data.get('data'),
                created_by_id=request.user.id
            )
            
            return Response({
                'success': True,
                'sent_count': count,
                'message': f'Broadcast enviado a {count} usuarios'
            })
        
        except Exception as e:
            logger.error(f"Error en broadcast: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Enviar broadcast a grupo",
        description="Envía una notificación a usuarios de un grupo específico",
    )
    @action(detail=False, methods=['post'])
    def broadcast_group(self, request: Request) -> Response:
        """Enviar broadcast a un grupo específico."""
        serializer = BroadcastNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        group_name = request.data.get('group_name')
        if not group_name:
            return Response(
                {'error': 'Nombre del grupo es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = NotificationBroadcastService()
            
            count = service.broadcast_to_user_group(
                group_name=group_name,
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                notification_type=NotificationType(serializer.validated_data['notification_type']),
                priority=NotificationPriority(serializer.validated_data['priority']),
                data=serializer.validated_data.get('data'),
                created_by_id=request.user.id
            )
            
            return Response({
                'success': True,
                'sent_count': count,
                'group': group_name,
                'message': f'Broadcast enviado a {count} usuarios del grupo {group_name}'
            })
        
        except Exception as e:
            logger.error(f"Error en broadcast a grupo: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
