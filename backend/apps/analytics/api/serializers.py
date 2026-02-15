"""
Serializers for the Analytics API.
"""

from rest_framework import serializers


class AnalyticsEventSerializer(serializers.Serializer):
    """Validates a single analytics event from the client."""

    event_type = serializers.ChoiceField(
        choices=[
            "pageview",
            "click",
            "search",
            "filter_change",
            "bill_view",
            "member_view",
            "vote_view",
            "share",
            "signup",
            "login",
            "chat_open",
            "follow",
        ]
    )
    timestamp = serializers.DateTimeField()
    page_path = serializers.CharField(max_length=2048)
    page_type = serializers.CharField(max_length=30, required=False, default="")
    metadata = serializers.JSONField(required=False, default=dict)
    referrer = serializers.CharField(max_length=2048, required=False, default="")


class EventBatchSerializer(serializers.Serializer):
    """Validates the batch payload from the analytics client."""

    anonymous_id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    user_id = serializers.CharField(required=False, allow_null=True, default=None)
    events = AnalyticsEventSerializer(many=True)
    user_agent = serializers.CharField(max_length=512, required=False, default="")
    referrer = serializers.CharField(max_length=2048, required=False, default="")

    def validate_events(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 events per batch")
        if len(value) == 0:
            raise serializers.ValidationError("At least one event is required")
        return value

    def validate_user_id(self, value):
        """Convert user_id string to int or None."""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
