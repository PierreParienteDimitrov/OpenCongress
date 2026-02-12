"""
Cache Service - Redis cache invalidation and ISR revalidation.
"""

import logging

import httpx
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheService:
    """Service for cache invalidation and ISR revalidation."""

    @staticmethod
    def invalidate_bill(bill_id: str) -> None:
        """Invalidate cache for a specific bill and trigger ISR."""
        # Clear Django cache keys related to this bill
        cache_keys = [
            f"bill_detail_{bill_id}",
            f"bill_summary_{bill_id}",
        ]
        for key in cache_keys:
            cache.delete(key)

        logger.info(f"Invalidated cache for bill {bill_id}")

        # Trigger ISR revalidation
        CacheService._trigger_isr_revalidation(f"/legislation/{bill_id}")

    @staticmethod
    def invalidate_member(bioguide_id: str, chamber: str) -> None:
        """Invalidate cache for a specific member and trigger ISR."""
        # Clear Django cache keys related to this member
        cache_keys = [
            f"member_detail_{bioguide_id}",
            f"member_bio_{bioguide_id}",
        ]
        for key in cache_keys:
            cache.delete(key)

        logger.info(f"Invalidated cache for member {bioguide_id}")

        # Trigger ISR revalidation
        route = "senator" if chamber == "senate" else "representative"
        CacheService._trigger_isr_revalidation(f"/{route}/{bioguide_id}")

    @staticmethod
    def invalidate_weekly_summary(year: int, week: int, summary_type: str) -> None:
        """Invalidate cache for a weekly summary and trigger ISR."""
        # Clear Django cache keys
        cache_keys = [
            f"weekly_summary_{year}_{week}_{summary_type}",
            "weekly_summaries_current",
        ]
        for key in cache_keys:
            cache.delete(key)

        logger.info(
            f"Invalidated cache for weekly summary {year}-W{week} {summary_type}"
        )

        # Trigger ISR revalidation for this-week page
        CacheService._trigger_isr_revalidation("/this-week")

    @staticmethod
    def _trigger_isr_revalidation(path: str) -> bool:
        """
        Trigger Next.js ISR revalidation for a specific path.

        Args:
            path: The path to revalidate (e.g., "/legislation/hr-1234-118")

        Returns:
            True if revalidation was triggered successfully, False otherwise
        """
        frontend_url = getattr(settings, "FRONTEND_URL", None)
        revalidation_secret = getattr(settings, "REVALIDATION_SECRET", None)

        if not frontend_url or not revalidation_secret:
            logger.warning(
                "FRONTEND_URL or REVALIDATION_SECRET not configured, skipping ISR"
            )
            return False

        try:
            revalidate_url = f"{frontend_url}/api/revalidate"
            response = httpx.post(
                revalidate_url,
                json={"path": path, "secret": revalidation_secret},
                timeout=10.0,
            )

            if response.status_code == 200:
                logger.info(f"Successfully triggered ISR revalidation for {path}")
                return True
            else:
                logger.warning(
                    f"ISR revalidation failed for {path}: {response.status_code}"
                )
                return False

        except httpx.RequestError as e:
            logger.error(f"Error triggering ISR revalidation for {path}: {e}")
            return False
