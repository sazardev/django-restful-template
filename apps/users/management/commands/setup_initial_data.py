"""
Setup Initial Data Command.
Comando para configurar datos iniciales del sistema.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from decimal import Decimal
import uuid

User = get_user_model()


class Command(BaseCommand):
    """Comando para configurar datos iniciales."""
    
    help = 'Configura datos iniciales del sistema incluyendo usuarios, grupos y permisos'

    def add_arguments(self, parser):
        """Agregar argumentos al comando."""
        parser.add_argument(
            '--with-demo-data',
            action='store_true',
            help='Incluir datos de demostración'
        )
        parser.add_argument(
            '--force',
            action='store_true', 
            help='Forzar recreación de datos existentes'
        )

    def handle(self, *args, **options):
        """Ejecutar comando."""
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando configuración de datos iniciales...')
        )

        try:
            with transaction.atomic():
                self.create_groups_and_permissions()
                self.create_superuser()
                self.create_initial_users()
                
                if options['with_demo_data']:
                    self.create_demo_data()

            self.stdout.write(
                self.style.SUCCESS('✅ Configuración completada exitosamente!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la configuración: {e}')
            )
            raise

    def create_groups_and_permissions(self):
        """Crear grupos y permisos del sistema."""
        self.stdout.write('📋 Creando grupos y permisos...')

        groups_data = [
            {
                'name': 'Administradores',
                'permissions': ['add_user', 'change_user', 'delete_user', 'view_user']
            },
            {
                'name': 'Transportistas',
                'permissions': ['view_user', 'add_vehicle', 'change_vehicle', 'view_vehicle']
            },
            {
                'name': 'Operadores Logísticos',
                'permissions': ['view_user', 'view_vehicle', 'view_auction']            },
            {
                'name': 'Clientes',
                'permissions': ['view_user']
            },
        ]

        for group_data in groups_data:
            group, created = Group.objects.get_or_create(name=group_data['name'])
            
            if created:
                self.stdout.write(f'  ✓ Grupo creado: {group.name}')
            else:
                self.stdout.write(f'  → Grupo existente: {group.name}')

    def create_superuser(self):
        """Crear superusuario por defecto."""
        self.stdout.write('👤 Creando superusuario...')

        if not User.objects.filter(email='admin@example.com').exists():
            superuser = User.objects.create_superuser(
                email='admin@example.com',
                username='admin',
                password='admin123',
                first_name='Admin',
                last_name='System',
                phone='+1234567890'
            )
            
            # Agregar al grupo de administradores
            admin_group = Group.objects.get(name='Administradores')
            superuser.groups.add(admin_group)
            
            self.stdout.write('  ✓ Superusuario creado: admin@example.com / admin123')
        else:
            self.stdout.write('  → Superusuario ya existe: admin@example.com')

    def create_initial_users(self):
        """Crear usuarios iniciales del sistema."""
        self.stdout.write('👥 Creando usuarios iniciales...')

        users_data = [
            {
                'email': 'transportista@example.com',
                'password': 'transport123',
                'first_name': 'Carlos',
                'last_name': 'Transportista',
                'phone_number': '+1234567891',
                'user_type': 'carrier',
                'group': 'Transportistas'
            },
            {
                'email': 'operador@example.com',
                'password': 'operator123',
                'first_name': 'Ana',
                'last_name': 'Operadora',
                'phone_number': '+1234567892',
                'user_type': 'logistics_operator',
                'group': 'Operadores Logísticos'
            },
            {
                'email': 'cliente@example.com',
                'password': 'client123',
                'first_name': 'Juan',
                'last_name': 'Cliente',
                'phone_number': '+1234567893',
                'user_type': 'customer',
                'group': 'Clientes'            },
        ]

        for user_data in users_data:
            if not User.objects.filter(email=user_data['email']).exists():
                user = User.objects.create_user(
                    username=user_data['email'].split('@')[0],  # Use email prefix as username
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    phone=user_data['phone_number'],
                    role=user_data['user_type']
                )
                
                # Agregar al grupo correspondiente
                group = Group.objects.get(name=user_data['group'])
                user.groups.add(group)
                
                self.stdout.write(f'  ✓ Usuario creado: {user.email}')
            else:
                self.stdout.write(f'  → Usuario existente: {user_data["email"]}')

    def create_demo_data(self):
        """Crear datos de demostración."""
        self.stdout.write('🎯 Creando datos de demostración...')
        
        # Aquí podrías agregar vehículos de ejemplo, subastas, etc.
        self.create_demo_vehicles()

    def create_demo_vehicles(self):
        """Crear vehículos de demostración."""
        self.stdout.write('🚛 Creando vehículos de demostración...')
        
        # Obtener transportista para asignar vehículos
        try:
            transportista = User.objects.get(email='transportista@example.com')
        except User.DoesNotExist:
            self.stdout.write('  ⚠ No se pudo encontrar transportista para crear vehículos')
            return

        # Esta sería la lógica para crear vehículos demo
        # Por ahora solo mostramos el mensaje
        self.stdout.write('  → Vehículos demo se crearían aquí')

    def create_demo_auctions(self):
        """Crear subastas de demostración."""
        self.stdout.write('🏷️ Creando subastas de demostración...')
        
        # Esta sería la lógica para crear subastas demo
        self.stdout.write('  → Subastas demo se crearían aquí')
