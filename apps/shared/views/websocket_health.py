"""
WebSocket health check endpoint.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_http_methods(["GET"])
def websocket_health(request):
    """
    Health check for WebSocket service.
    """
    return JsonResponse({
        "status": "healthy",
        "service": "Django WebSocket Server",
        "type": "websocket"
    })
