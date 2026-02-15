"""
Analytics aggregation and identity resolution tasks.
"""

import logging
import re
from datetime import timedelta

from celery import shared_task
from django.db.models import Count, Q
from django.db.models.functions import TruncHour
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def aggregate_pageviews_hourly(self) -> dict:
    """
    Aggregate the last 2 hours of pageview events into PageViewRollup rows.

    Runs every hour. Uses a 2-hour lookback window for safety
    (handles late-arriving events from the previous hour).
    """
    from apps.analytics.models import AnalyticsEvent, PageViewRollup

    try:
        cutoff = timezone.now() - timedelta(hours=2)

        events_qs = (
            AnalyticsEvent.objects.filter(
                event_type="pageview",
                timestamp__gte=cutoff,
            )
            .annotate(hour=TruncHour("timestamp"))
            .values("hour", "page_path", "page_type")
            .annotate(
                view_count=Count("id"),
                unique_sessions=Count("session_id", distinct=True),
                unique_users=Count(
                    "user_id",
                    distinct=True,
                    filter=Q(user_id__isnull=False),
                ),
            )
        )

        created = 0
        updated = 0

        for row in events_qs:
            entity_id = _extract_entity_id(row["page_path"], row["page_type"])

            _, was_created = PageViewRollup.objects.update_or_create(
                hour=row["hour"],
                page_path=row["page_path"],
                defaults={
                    "page_type": row["page_type"] or "",
                    "entity_id": entity_id,
                    "view_count": row["view_count"],
                    "unique_sessions": row["unique_sessions"],
                    "unique_users": row["unique_users"],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(f"Pageview aggregation: {created} created, {updated} updated")
        return {"success": True, "created": created, "updated": updated}

    except Exception as e:
        logger.error(f"Pageview aggregation failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def resolve_identities(self) -> dict:
    """
    Backfill user_id on events and sessions for recently linked identities.

    Runs daily. Finds IdentityLink records created in the last 48 hours,
    then updates all events and sessions for those anonymous_ids.
    """
    from apps.analytics.models import (
        AnalyticsEvent,
        AnalyticsSession,
        IdentityLink,
    )

    try:
        cutoff = timezone.now() - timedelta(hours=48)
        recent_links = IdentityLink.objects.filter(linked_at__gte=cutoff)

        total_events_updated = 0
        total_sessions_updated = 0

        for link in recent_links:
            events_updated = AnalyticsEvent.objects.filter(
                anonymous_id=link.anonymous_id,
                user_id__isnull=True,
            ).update(user_id=link.user_id)

            sessions_updated = AnalyticsSession.objects.filter(
                anonymous_id=link.anonymous_id,
                user_id__isnull=True,
            ).update(user_id=link.user_id)

            total_events_updated += events_updated
            total_sessions_updated += sessions_updated

        logger.info(
            f"Identity resolution: {total_events_updated} events, "
            f"{total_sessions_updated} sessions updated"
        )
        return {
            "success": True,
            "events_updated": total_events_updated,
            "sessions_updated": total_sessions_updated,
        }

    except Exception as e:
        logger.error(f"Identity resolution failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1)
def cleanup_old_events(self) -> dict:
    """
    Delete raw events older than 90 days. Rollup data is kept indefinitely.

    Runs weekly. Raw event data is the high-volume table; rollups
    are compact enough to retain for trend analysis.
    """
    from apps.analytics.models import AnalyticsEvent, AnalyticsSession

    try:
        cutoff = timezone.now() - timedelta(days=90)

        events_deleted, _ = AnalyticsEvent.objects.filter(timestamp__lt=cutoff).delete()

        sessions_deleted, _ = AnalyticsSession.objects.filter(
            started_at__lt=cutoff
        ).delete()

        logger.info(
            f"Analytics cleanup: {events_deleted} events, "
            f"{sessions_deleted} sessions deleted"
        )
        return {
            "success": True,
            "events_deleted": events_deleted,
            "sessions_deleted": sessions_deleted,
        }

    except Exception as e:
        logger.error(f"Analytics cleanup failed: {e}")
        raise self.retry(exc=e)


def _extract_entity_id(page_path: str, page_type: str) -> str:
    """
    Extract the entity primary key from a page_path.

    Examples:
        /legislation/hr1234-119 -> "hr1234-119"
        /senate/S0001-john-doe  -> "S0001"
        /vote/house-119-1-123   -> "house-119-1-123"
        /committees/HSAG00      -> "HSAG00"
    """
    if not page_path or not page_type:
        return ""

    path = page_path.rstrip("/")
    segments = path.split("/")

    if len(segments) < 2:
        return ""

    last_segment = segments[-1]

    if page_type in ("bill", "bill_detail"):
        return last_segment

    if page_type in ("member", "member_profile"):
        match = re.match(r"^([A-Z]\d+)", last_segment)
        if match:
            return match.group(1)

    if page_type in ("vote", "vote_detail"):
        return last_segment

    if page_type in ("committee",):
        match = re.match(r"^([A-Z0-9]+)", last_segment)
        if match:
            return match.group(1)

    return last_segment
