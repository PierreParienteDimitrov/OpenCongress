"""
Views for the Analytics API.
"""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.analytics.models import AnalyticsEvent, AnalyticsSession, IdentityLink

from .serializers import EventBatchSerializer

logger = logging.getLogger(__name__)


class AnalyticsEventThrottle(AnonRateThrottle):
    """Higher rate limit for analytics events (IP-based)."""

    rate = "600/hour"


class EventIngestView(APIView):
    """
    POST /api/v1/analytics/events/

    Accepts a batch of analytics events. No authentication required.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnalyticsEventThrottle]

    def post(self, request):
        serializer = EventBatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        anonymous_id = data["anonymous_id"]
        session_id = data["session_id"]
        user_id = data.get("user_id")

        ua = data.get("user_agent", "") or request.META.get("HTTP_USER_AGENT", "")
        device_type = _parse_device_type(ua)

        session, _ = AnalyticsSession.objects.get_or_create(
            id=session_id,
            defaults={
                "anonymous_id": anonymous_id,
                "user_id": user_id,
                "referrer": data.get("referrer", ""),
                "user_agent": ua[:512],
                "device_type": device_type,
            },
        )

        # Update session if user logged in since session started
        if user_id and not session.user_id:
            session.user_id = user_id
            session.save(update_fields=["user_id", "last_seen_at"])

        event_objects = [
            AnalyticsEvent(
                session=session,
                anonymous_id=anonymous_id,
                user_id=user_id,
                event_type=event["event_type"],
                timestamp=event["timestamp"],
                page_path=event["page_path"][:2048],
                page_type=event.get("page_type", ""),
                metadata=event.get("metadata", {}),
                referrer=event.get("referrer", ""),
            )
            for event in data["events"]
        ]

        AnalyticsEvent.objects.bulk_create(event_objects)

        # Create identity link for future backfill
        if user_id:
            IdentityLink.objects.get_or_create(
                anonymous_id=anonymous_id,
                user_id=user_id,
            )

        return Response(
            {"accepted": len(event_objects)},
            status=status.HTTP_202_ACCEPTED,
        )


def _parse_device_type(ua: str) -> str:
    """Simple UA-based device classification."""
    ua_lower = ua.lower()
    if "mobile" in ua_lower or "android" in ua_lower:
        if "tablet" in ua_lower or "ipad" in ua_lower:
            return "tablet"
        return "mobile"
    if "ipad" in ua_lower:
        return "tablet"
    return "desktop"
