"""
Analytics models for OpenCongress.

Stores raw events from the frontend analytics client, session tracking,
hourly pageview rollups, and identity links for anonymous-to-authenticated
user resolution.
"""

import uuid

from django.db import models


class AnalyticsSession(models.Model):
    """A browsing session, grouping events from a single visit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anonymous_id = models.UUIDField(
        db_index=True,
        help_text="Client-generated UUID persisted in localStorage",
    )
    user_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Django User.id, set when authenticated",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    referrer = models.URLField(max_length=2048, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    device_type = models.CharField(
        max_length=10,
        blank=True,
        help_text="desktop | mobile | tablet",
    )

    class Meta:
        db_table = "analytics_sessions"
        indexes = [
            models.Index(fields=["anonymous_id", "-started_at"]),
            models.Index(fields=["user_id", "-started_at"]),
            models.Index(fields=["-started_at"]),
        ]

    def __str__(self):
        return f"Session {self.id} (anon={self.anonymous_id})"


class AnalyticsEvent(models.Model):
    """A single analytics event (pageview, click, search, etc.)."""

    class EventType(models.TextChoices):
        PAGEVIEW = "pageview", "Page View"
        CLICK = "click", "Click"
        SEARCH = "search", "Search"
        FILTER_CHANGE = "filter_change", "Filter Change"
        BILL_VIEW = "bill_view", "Bill View"
        MEMBER_VIEW = "member_view", "Member View"
        VOTE_VIEW = "vote_view", "Vote View"
        SHARE = "share", "Share"
        SIGNUP = "signup", "Sign Up"
        LOGIN = "login", "Login"
        CHAT_OPEN = "chat_open", "Chat Open"
        FOLLOW = "follow", "Follow Member"

    id = models.BigAutoField(primary_key=True)

    session = models.ForeignKey(
        AnalyticsSession,
        on_delete=models.CASCADE,
        related_name="events",
    )
    anonymous_id = models.UUIDField(
        help_text="Denormalized from session for direct queries",
    )
    user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Django User.id, set when authenticated",
    )

    event_type = models.CharField(max_length=30, choices=EventType.choices)
    timestamp = models.DateTimeField(
        help_text="Client-reported event time (ISO 8601)",
    )

    page_path = models.CharField(
        max_length=2048,
        help_text="URL path, e.g. /legislation/hr1234-119",
    )
    page_type = models.CharField(
        max_length=30,
        blank=True,
        help_text="bill | vote | member | chamber | committee | calendar | home",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Event-specific data: button_id, search_query, entity_id, etc.",
    )

    referrer = models.URLField(max_length=2048, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_events"
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["event_type", "-timestamp"]),
            models.Index(fields=["page_type", "-timestamp"]),
            models.Index(fields=["anonymous_id", "-timestamp"]),
            models.Index(fields=["user_id", "-timestamp"]),
            models.Index(fields=["session_id", "-timestamp"]),
            models.Index(
                fields=["event_type", "page_path", "-timestamp"],
                name="event_path_time_idx",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.page_path} ({self.timestamp})"


class PageViewRollup(models.Model):
    """
    Hourly aggregation of pageviews per page_path and page_type.

    Populated by a Celery periodic task. Enables fast queries like
    "top 10 bills by views this week" without scanning the event table.
    """

    id = models.BigAutoField(primary_key=True)
    hour = models.DateTimeField(help_text="Truncated to the hour")
    page_path = models.CharField(max_length=2048)
    page_type = models.CharField(max_length=30, blank=True)

    entity_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary key of the viewed entity, if applicable",
    )

    view_count = models.IntegerField(default=0)
    unique_sessions = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)

    class Meta:
        db_table = "analytics_pageview_rollups"
        unique_together = ("hour", "page_path")
        indexes = [
            models.Index(fields=["page_type", "-hour"]),
            models.Index(fields=["entity_id", "-hour"]),
            models.Index(fields=["-hour"]),
        ]

    def __str__(self):
        return f"{self.page_path} @ {self.hour}: {self.view_count} views"


class IdentityLink(models.Model):
    """
    Maps anonymous_id to user_id after login.

    When a user logs in, we create an IdentityLink record. A Celery task
    then backfills user_id on all prior events for that anonymous_id.
    """

    id = models.BigAutoField(primary_key=True)
    anonymous_id = models.UUIDField(db_index=True)
    user_id = models.IntegerField(db_index=True)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_identity_links"
        unique_together = ("anonymous_id", "user_id")

    def __str__(self):
        return f"anon:{self.anonymous_id} -> user:{self.user_id}"
