"""
Health check views for system monitoring and status verification.
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import sys
import os
from datetime import datetime


class HealthCheckView(APIView):
    """
    Endpoint básico de health check.
    Verifica que la aplicación esté funcionando.
    """
    
    def get(self, request):
        """Retorna estado básico de salud del sistema."""
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'django-restful-template',
            'version': '1.0.0'
        })


class DetailedHealthCheckView(APIView):
    """
    Endpoint detallado de health check.
    Verifica componentes críticos del sistema.
    """
    
    def get(self, request):
        """Retorna estado detallado de salud del sistema."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'django-restful-template',
            'version': '1.0.0',
            'checks': {}
        }
        
        # Verificar base de datos
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_status['checks']['database'] = {
                    'status': 'healthy',
                    'message': 'Database connection successful'
                }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_status['status'] = 'unhealthy'
        
        # Verificar cache
        try:
            cache.set('health_check', 'test', 30)
            cache_value = cache.get('health_check')
            if cache_value == 'test':
                health_status['checks']['cache'] = {
                    'status': 'healthy',
                    'message': 'Cache connection successful'
                }
            else:
                health_status['checks']['cache'] = {
                    'status': 'unhealthy',
                    'message': 'Cache test failed'
                }
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'message': f'Cache connection failed: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Verificar sistema de archivos
        try:
            test_file_path = '/tmp/health_check_test.txt'
            with open(test_file_path, 'w') as f:
                f.write('test')
            os.remove(test_file_path)
            health_status['checks']['filesystem'] = {
                'status': 'healthy',
                'message': 'File system access successful'
            }
        except Exception as e:
            health_status['checks']['filesystem'] = {
                'status': 'unhealthy',
                'message': f'File system access failed: {str(e)}'
            }
            health_status['status'] = 'degraded'
        
        # Información del sistema
        health_status['system_info'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'memory_usage': self._get_memory_usage()
        }
        
        # Determinar status code HTTP basado en el estado
        status_code = status.HTTP_200_OK
        if health_status['status'] == 'unhealthy':
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_status['status'] == 'degraded':
            status_code = status.HTTP_206_PARTIAL_CONTENT
        
        return Response(health_status, status=status_code)
    
    def _get_memory_usage(self):
        """Obtener información básica de uso de memoria."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {
                'message': 'psutil not available for memory monitoring'
            }
        except Exception as e:
            return {
                'error': str(e)
            }


class ReadinessView(APIView):
    """
    Endpoint de readiness check.
    Verifica que la aplicación esté lista para recibir tráfico.
    """
    
    def get(self, request):
        """Verificar si la aplicación está lista."""
        # Verificar que las migraciones estén aplicadas
        try:
            from django.core.management import execute_from_command_line
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connections
            
            executor = MigrationExecutor(connections['default'])
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                return Response({
                    'status': 'not_ready',
                    'message': 'Pending migrations found',
                    'pending_migrations': len(plan)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Migration check failed: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({
            'status': 'ready',
            'timestamp': datetime.now().isoformat(),
            'message': 'Application is ready to receive traffic'
        })


class LivenessView(APIView):
    """
    Endpoint de liveness check.
    Verifica que la aplicación esté viva (no en deadlock).
    """
    
    def get(self, request):
        """Verificar que la aplicación esté viva."""
        return Response({
            'status': 'alive',
            'timestamp': datetime.now().isoformat(),
            'uptime': self._get_uptime(),
            'pid': os.getpid()
        })
    
    def _get_uptime(self):
        """Calcular uptime básico."""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds
        except:
            return 'unknown'


# Vista simple para compatibilidad con sistemas legacy
def simple_health_check(request):
    """Vista simple de health check que retorna 200 OK."""
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })
