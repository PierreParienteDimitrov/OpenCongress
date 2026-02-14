"""
Infrastructure monitoring tasks.

Periodically checks service health and posts results to Discord.
"""

import logging
from datetime import datetime, timezone

import httpx
from celery import shared_task
from django.conf import settings
from django.db import connection
from redis import Redis

from services.discord import AlertLevel, send_discord_message

logger = logging.getLogger(__name__)


def _check_database() -> tuple[bool, str]:
    """Check database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True, "Connected"
    except Exception as e:
        return False, str(e)


def _check_redis() -> tuple[bool, str]:
    """Check Redis connectivity."""
    try:
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        client = Redis.from_url(redis_url, socket_connect_timeout=5)
        client.ping()
        return True, "Connected"
    except Exception as e:
        return False, str(e)


def _check_frontend() -> tuple[bool, str]:
    """Check frontend accessibility via HTTP GET."""
    frontend_url = getattr(settings, "FRONTEND_URL", "")
    if not frontend_url:
        return True, "Not configured (skipped)"
    try:
        response = httpx.get(frontend_url, timeout=10, follow_redirects=True)
        if response.status_code < 500:
            return True, f"HTTP {response.status_code}"
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def _check_celery_workers() -> tuple[bool, str]:
    """Check if at least one Celery worker is responding."""
    from config.celery import app as celery_app

    try:
        inspect = celery_app.control.inspect(timeout=5)
        active = inspect.active()
        if active is None:
            return False, "No workers responding"
        worker_count = len(active)
        return True, f"{worker_count} worker(s) active"
    except Exception as e:
        return False, str(e)


def _run_all_checks() -> dict[str, tuple[bool, str]]:
    """Run all health checks and return results."""
    return {
        "Database": _check_database(),
        "Redis": _check_redis(),
        "Frontend": _check_frontend(),
        "Celery Workers": _check_celery_workers(),
    }


@shared_task(bind=True, max_retries=0)
def run_health_check(self) -> dict:
    """
    Run infrastructure health checks every 5 minutes.

    Checks: Database, Redis, Frontend, Celery workers.
    Posts to Discord only on failure.
    """
    checks = _run_all_checks()

    results = {}
    failures = []

    for name, (healthy, detail) in checks.items():
        status = "OK" if healthy else "FAIL"
        results[name] = {"status": status, "detail": detail}
        if not healthy:
            failures.append(f"{name}: {detail}")

    if failures:
        send_discord_message(
            title="Health Check Failed",
            description=f"{len(failures)} check(s) failed",
            level=AlertLevel.ERROR,
            fields=[
                {
                    "name": name,
                    "value": f"{r['status']}: {r['detail']}",
                }
                for name, r in results.items()
            ],
        )
        logger.error(f"Health check failures: {failures}")
    else:
        logger.info("All health checks passed")

    return {"success": len(failures) == 0, "checks": results}


@shared_task(bind=True, max_retries=0)
def daily_health_summary(self) -> dict:
    """
    Post a daily health summary to Discord at 9am ET.

    Always posts regardless of status (green or issues).
    """
    checks = _run_all_checks()

    all_healthy = all(healthy for healthy, _ in checks.values())
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    if all_healthy:
        send_discord_message(
            title="Daily Health Report",
            description=f"All systems operational as of {timestamp}",
            level=AlertLevel.INFO,
            fields=[
                {"name": name, "value": f"OK: {detail}"}
                for name, (_, detail) in checks.items()
            ],
        )
    else:
        failures = [name for name, (healthy, _) in checks.items() if not healthy]
        send_discord_message(
            title="Daily Health Report — Issues Found",
            description=f"{len(failures)} service(s) unhealthy as of {timestamp}",
            level=AlertLevel.WARNING,
            fields=[
                {
                    "name": name,
                    "value": f"{'OK' if healthy else 'FAIL'}: {detail}",
                }
                for name, (healthy, detail) in checks.items()
            ],
        )

    return {"all_healthy": all_healthy, "timestamp": now.isoformat()}
