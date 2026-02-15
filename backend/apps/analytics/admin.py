from django.contrib import admin

from .models import AnalyticsEvent, AnalyticsSession, IdentityLink, PageViewRollup


@admin.register(AnalyticsSession)
class AnalyticsSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "anonymous_id",
        "user_id",
        "device_type",
        "started_at",
        "last_seen_at",
    ]
    list_filter = ["device_type", "started_at"]
    search_fields = ["anonymous_id", "user_id"]
    ordering = ["-started_at"]
    readonly_fields = [
        "id",
        "anonymous_id",
        "user_id",
        "referrer",
        "user_agent",
        "device_type",
        "started_at",
        "last_seen_at",
    ]


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "event_type",
        "page_path",
        "page_type",
        "user_id",
        "timestamp",
    ]
    list_filter = ["event_type", "page_type", "timestamp"]
    search_fields = ["page_path", "anonymous_id", "user_id"]
    ordering = ["-timestamp"]
    readonly_fields = [
        "id",
        "session",
        "anonymous_id",
        "user_id",
        "event_type",
        "timestamp",
        "page_path",
        "page_type",
        "metadata",
        "referrer",
        "created_at",
    ]


@admin.register(PageViewRollup)
class PageViewRollupAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "page_path",
        "page_type",
        "entity_id",
        "view_count",
        "unique_sessions",
        "unique_users",
        "hour",
    ]
    list_filter = ["page_type", "hour"]
    search_fields = ["page_path", "entity_id"]
    ordering = ["-hour"]


@admin.register(IdentityLink)
class IdentityLinkAdmin(admin.ModelAdmin):
    list_display = ["id", "anonymous_id", "user_id", "linked_at"]
    search_fields = ["anonymous_id", "user_id"]
    ordering = ["-linked_at"]
    readonly_fields = ["id", "anonymous_id", "user_id", "linked_at"]
