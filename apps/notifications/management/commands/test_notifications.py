"""
Test Notifications Command.
Comando para probar el sistema de notificaciones.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.notifications.application.services import (
    NotificationApplicationService, NotificationBroadcastService
)
from apps.notifications.domain.entities import NotificationType, NotificationPriority

User = get_user_model()


class Command(BaseCommand):
    """Comando para probar notificaciones."""
    
    help = 'Prueba el sistema de notificaciones con datos de ejemplo'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email del usuario para recibir notificaciones de prueba'
        )
        parser.add_argument(
            '--broadcast',
            action='store_true',
            help='Enviar notificación broadcast a todos los usuarios'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Número de notificaciones de prueba a crear'
        )
    
    def handle(self, *args, **options):
        """Ejecutar comando."""
        self.stdout.write(
            self.style.SUCCESS('🔔 Iniciando pruebas del sistema de notificaciones...')
        )
        
        # Obtener usuario para pruebas
        user_email = options.get('user_email')
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Usuario no encontrado: {user_email}')
                )
                return
        else:
            # Usar el primer superusuario disponible
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('❌ No hay superusuarios disponibles')
                )
                return
        
        self.stdout.write(f'👤 Usuario de prueba: {user.email}')
        
        # Probar servicios de notificación
        self.test_notification_service(user, options.get('count', 5))
        
        if options.get('broadcast'):
            self.test_broadcast_service()
        
        # Mostrar estadísticas
        self.show_statistics(user)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Pruebas de notificaciones completadas')
        )
    
    def test_notification_service(self, user, count):
        """Probar servicio de notificaciones."""
        self.stdout.write('\n📝 Creando notificaciones de prueba...')
        
        service = NotificationApplicationService()
        
        # Crear diferentes tipos de notificaciones
        notification_tests = [
            {
                'title': 'Bienvenido al sistema',
                'message': 'Gracias por unirte a nuestro sistema de gestión logística.',
                'type': NotificationType.SUCCESS,
                'priority': NotificationPriority.NORMAL,
                'data': {'welcome': True, 'user_type': 'new'}
            },
            {
                'title': 'Nueva subasta disponible',
                'message': 'Se ha creado una nueva subasta para un vehículo que te puede interesar.',
                'type': NotificationType.INFO,
                'priority': NotificationPriority.HIGH,
                'data': {'auction_id': 'test-123', 'vehicle_type': 'camion'}
            },
            {
                'title': '¡Tu puja ha sido superada!',
                'message': 'Alguien ha pujado más alto en la subasta del camión Mercedes.',
                'type': NotificationType.WARNING,
                'priority': NotificationPriority.HIGH,
                'data': {'auction_id': 'test-456', 'new_bid': 50000}
            },
            {
                'title': 'Mantenimiento programado',
                'message': 'El sistema estará en mantenimiento mañana de 2:00 a 4:00 AM.',
                'type': NotificationType.WARNING,
                'priority': NotificationPriority.NORMAL,
                'data': {'maintenance': True, 'scheduled_time': '2025-06-15 02:00:00'}
            },
            {
                'title': 'Error en el procesamiento',
                'message': 'Hubo un error al procesar tu última solicitud. Por favor, inténtalo de nuevo.',
                'type': NotificationType.ERROR,
                'priority': NotificationPriority.URGENT,
                'data': {'error_code': 'E001', 'retry_possible': True}
            }
        ]
        
        created_count = 0
        for i in range(min(count, len(notification_tests))):
            try:
                test_data = notification_tests[i]
                notification = service.create_notification(
                    user_id=user.id,
                    title=test_data['title'],
                    message=test_data['message'],
                    notification_type=test_data['type'],
                    priority=test_data['priority'],
                    data=test_data['data'],
                    send_realtime=True
                )
                
                self.stdout.write(
                    f'  ✅ Creada: {notification.title} (ID: {notification.id})'
                )
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error creando notificación: {e}')
                )
        
        self.stdout.write(f'📊 Total creadas: {created_count} notificaciones')
    
    def test_broadcast_service(self):
        """Probar servicio de broadcast."""
        self.stdout.write('\n📢 Enviando notificación broadcast...')
        
        try:
            service = NotificationBroadcastService()
            count = service.broadcast_to_all_users(
                title='Mensaje del sistema',
                message='Esta es una notificación de prueba enviada a todos los usuarios activos.',
                notification_type=NotificationType.INFO,
                priority=NotificationPriority.NORMAL,
                data={'broadcast': True, 'test': True}
            )
            
            self.stdout.write(f'  ✅ Broadcast enviado a {count} usuarios')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Error en broadcast: {e}')
            )
    
    def show_statistics(self, user):
        """Mostrar estadísticas de notificaciones."""
        self.stdout.write('\n📈 Estadísticas de notificaciones:')
        
        try:
            service = NotificationApplicationService()
            
            # Obtener estadísticas del usuario
            total_notifications = len(service.get_user_notifications(user.id))
            unread_count = service.get_unread_count(user.id)
            read_count = total_notifications - unread_count
            
            self.stdout.write(f'  👤 Usuario: {user.email}')
            self.stdout.write(f'  📧 Total de notificaciones: {total_notifications}')
            self.stdout.write(f'  ✉️  No leídas: {unread_count}')
            self.stdout.write(f'  ✅ Leídas: {read_count}')
            
            # Mostrar notificaciones recientes
            recent_notifications = service.get_user_notifications(
                user.id, unread_only=False, limit=3
            )
            
            if recent_notifications:
                self.stdout.write('\n📋 Últimas 3 notificaciones:')
                for notification in recent_notifications:
                    status = '✉️' if not notification.is_read else '✅'
                    self.stdout.write(
                        f'  {status} {notification.title} - {notification.notification_type.value}'
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error obteniendo estadísticas: {e}')
            )
