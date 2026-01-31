"""
Health check views for monitoring and CI/CD pipelines.
"""

from django.db import connection
from django.http import JsonResponse
from redis import Redis
from django.conf import settings


def health_check(request):
    """
    Health check endpoint for load balancers and CI/CD pipelines.
    Returns 200 if the service is healthy, 503 if any dependency is unhealthy.
    """
    health = {
        "status": "healthy",
        "database": "healthy",
        "redis": "healthy",
    }
    status_code = 200

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        health["database"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
        status_code = 503

    # Check Redis
    try:
        redis_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        redis_client.ping()
    except Exception as e:
        health["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
        status_code = 503

    return JsonResponse(health, status=status_code)


def ready_check(request):
    """
    Readiness check - returns 200 when the app is ready to receive traffic.
    Used by Kubernetes/Railway for rolling deployments.
    """
    return JsonResponse({"status": "ready"})
