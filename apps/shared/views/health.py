"""
Health check endpoints for Django application.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.core.cache import cache
import redis
from celery import current_app


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint.
    """
    return JsonResponse({
        "status": "healthy",
        "service": "Django RESTful Logistics Template",
        "version": "1.0.0"
    })


@csrf_exempt
@require_http_methods(["GET"])
def health_check_detailed(request):
    """
    Detailed health check with service dependencies.
    """
    checks = {
        "database": check_database(),
        "cache": check_cache(),
        "redis": check_redis(),
        "celery": check_celery(),
    }
    
    overall_status = "healthy" if all(
        check["status"] == "healthy" for check in checks.values()
    ) else "unhealthy"
    
    return JsonResponse({
        "status": overall_status,
        "service": "Django RESTful Logistics Template",
        "version": "1.0.0",
        "checks": checks
    })


def check_database():
    """Check database connectivity."""
    try:
        connection = connections['default']
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database error: {str(e)}"}


def check_cache():
    """Check cache connectivity."""
    try:
        cache.set("health_check", "test", 30)
        value = cache.get("health_check")
        if value == "test":
            return {"status": "healthy", "message": "Cache working correctly"}
        else:
            return {"status": "unhealthy", "message": "Cache not returning expected value"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Cache error: {str(e)}"}


def check_redis():
    """Check Redis connectivity."""
    try:
        # This is a basic Redis check
        # You might want to use the same Redis instance as configured in settings
        import redis
        from django.conf import settings
        
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        return {"status": "healthy", "message": "Redis connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Redis error: {str(e)}"}


def check_celery():
    """Check Celery connectivity."""
    try:
        # Check if we can inspect Celery workers
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            active_workers = len(stats)
            return {
                "status": "healthy", 
                "message": f"Celery working with {active_workers} active workers"
            }
        else:
            return {"status": "unhealthy", "message": "No Celery workers found"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Celery error: {str(e)}"}
