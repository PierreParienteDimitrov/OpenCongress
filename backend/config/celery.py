"""
Celery configuration for CongressTrack project.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("congresstrack")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(["tasks"])

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Data Synchronization
    "sync-votes-hourly-weekdays": {
        "task": "tasks.sync.sync_recent_votes",
        "schedule": crontab(minute=0, hour="9-21", day_of_week="1-5"),
        "options": {"queue": "sync"},
    },
    "sync-members-weekly": {
        "task": "tasks.sync.sync_members",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),
        "options": {"queue": "sync"},
    },
    # AI Content Generation
    "generate-daily-summaries": {
        "task": "tasks.ai.generate_bill_summaries",
        "schedule": crontab(minute=30, hour=6),
        "options": {"queue": "ai"},
    },
    "generate-weekly-trends": {
        "task": "tasks.ai.generate_trend_report",
        "schedule": crontab(minute=0, hour=3, day_of_week=6),
        "options": {"queue": "ai"},
    },
    # Notifications
    "send-weekly-forecast": {
        "task": "tasks.notifications.send_weekly_forecast",
        "schedule": crontab(minute=0, hour=18, day_of_week=0),
        "options": {"queue": "notifications"},
    },
    "send-weekly-recap": {
        "task": "tasks.notifications.send_weekly_recap",
        "schedule": crontab(minute=0, hour=10, day_of_week=6),
        "options": {"queue": "notifications"},
    },
    # Health Monitoring
    "health-check-5min": {
        "task": "tasks.monitoring.run_health_check",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "default"},
    },
    "daily-health-summary": {
        "task": "tasks.monitoring.daily_health_summary",
        "schedule": crontab(minute=0, hour=9),
        "options": {"queue": "default"},
    },
}

# Queue routing
app.conf.task_routes = {
    "tasks.sync.*": {"queue": "sync"},
    "tasks.ai.*": {"queue": "ai"},
    "tasks.notifications.*": {"queue": "notifications"},
    "tasks.monitoring.*": {"queue": "default"},
}

# Task settings
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = 1
