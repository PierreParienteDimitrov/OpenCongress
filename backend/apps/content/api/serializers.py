"""
Content API serializers.
"""

from rest_framework import serializers

from apps.content.models import DailySummary, WeeklySummary


class WeeklySummarySerializer(serializers.ModelSerializer):
    """Serializer for WeeklySummary model."""

    summary_type_display = serializers.CharField(
        source="get_summary_type_display", read_only=True
    )

    class Meta:
        model = WeeklySummary
        fields = [
            "id",
            "year",
            "week_number",
            "summary_type",
            "summary_type_display",
            "content",
            "model_used",
            "prompt_version",
            "tokens_used",
            "votes_included",
            "bills_included",
            "created_at",
        ]
        read_only_fields = fields


class WeeklySummaryListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    summary_type_display = serializers.CharField(
        source="get_summary_type_display", read_only=True
    )

    class Meta:
        model = WeeklySummary
        fields = [
            "id",
            "year",
            "week_number",
            "summary_type",
            "summary_type_display",
            "created_at",
        ]
        read_only_fields = fields


class DailySummarySerializer(serializers.ModelSerializer):
    """Serializer for DailySummary model."""

    summary_type_display = serializers.CharField(
        source="get_summary_type_display", read_only=True
    )

    class Meta:
        model = DailySummary
        fields = [
            "id",
            "date",
            "summary_type",
            "summary_type_display",
            "content",
            "model_used",
            "prompt_version",
            "tokens_used",
            "votes_included",
            "bills_included",
            "created_at",
        ]
        read_only_fields = fields


class DailySummaryListSerializer(serializers.ModelSerializer):
    """Lighter serializer for daily summary list views."""

    summary_type_display = serializers.CharField(
        source="get_summary_type_display", read_only=True
    )

    class Meta:
        model = DailySummary
        fields = [
            "id",
            "date",
            "summary_type",
            "summary_type_display",
            "created_at",
        ]
        read_only_fields = fields
