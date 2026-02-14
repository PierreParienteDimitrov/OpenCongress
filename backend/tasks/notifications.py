"""
Notification tasks.

Stubs for tasks referenced in the Celery beat schedule.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_weekly_forecast():
    """Send weekly forecast notifications. Not yet implemented."""
    logger.info("send_weekly_forecast: not yet implemented")
    return {"status": "not_implemented"}


@shared_task
def send_weekly_recap():
    """Send weekly recap notifications. Not yet implemented."""
    logger.info("send_weekly_recap: not yet implemented")
    return {"status": "not_implemented"}
