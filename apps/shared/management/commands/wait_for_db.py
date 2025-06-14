"""
Django command to wait for database to be available.
"""
import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.color import no_style


class Command(BaseCommand):
    """Django command to wait for database."""
    
    help = 'Wait for database to be available'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout in seconds (default: 30)'
        )
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to check (default: default)'
        )
    
    def handle(self, *args, **options):
        timeout = options['timeout']
        database = options['database']
        
        self.stdout.write(f'Waiting for database "{database}" to be available...')
        
        start_time = time.time()
        
        while True:
            try:
                # Try to get database connection
                connection = connections[database]
                
                # Try to execute a simple query
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Database "{database}" is available!')
                )
                break
                
            except OperationalError as e:
                elapsed_time = time.time() - start_time
                
                if elapsed_time >= timeout:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Database "{database}" is still not available after {timeout} seconds.'
                        )
                    )
                    self.stdout.write(
                        self.style.ERROR(f'Last error: {e}')
                    )
                    exit(1)
                
                self.stdout.write(
                    f'Database "{database}" not available yet... '
                    f'({elapsed_time:.1f}s/{timeout}s) - {e}'
                )
                time.sleep(1)
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Unexpected error: {e}')
                )
                exit(1)
