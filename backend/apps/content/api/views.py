"""
Content API views.
"""

from datetime import date

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.content.models import WeeklySummary

from .serializers import WeeklySummaryListSerializer, WeeklySummarySerializer


class WeeklySummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for weekly summaries.

    Provides endpoints for:
    - List all weekly summaries
    - Get current week's summaries
    - Get summaries for a specific week
    """

    queryset = WeeklySummary.objects.all().order_by("-year", "-week_number")
    serializer_class = WeeklySummarySerializer

    def get_serializer_class(self):
        if self.action == "list":
            return WeeklySummaryListSerializer
        return WeeklySummarySerializer

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60))  # Cache for 1 hour
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def current(self, request):
        """
        Get the current week's summaries (recap and preview).
        Returns both if available.
        """
        today = date.today()
        year, week_number, _ = today.isocalendar()

        summaries = WeeklySummary.objects.filter(year=year, week_number=week_number)

        # If no summaries for current week, try previous week
        if not summaries.exists():
            if week_number > 1:
                summaries = WeeklySummary.objects.filter(
                    year=year, week_number=week_number - 1
                )
            else:
                # First week of year, check last week of previous year
                summaries = WeeklySummary.objects.filter(year=year - 1, week_number=52)

        serializer = WeeklySummarySerializer(summaries, many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["get"], url_path="week/(?P<year>[0-9]+)/(?P<week>[0-9]+)"
    )
    @method_decorator(cache_page(60 * 60 * 24))  # Cache for 24 hours
    def week(self, request, year=None, week=None):
        """
        Get summaries for a specific week.

        Args:
            year: The year (e.g., 2024)
            week: The ISO week number (1-53)
        """
        try:
            year = int(year)
            week = int(week)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid year or week number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if week < 1 or week > 53:
            return Response(
                {"error": "Week number must be between 1 and 53"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summaries = WeeklySummary.objects.filter(year=year, week_number=week)

        if not summaries.exists():
            return Response(
                {"error": f"No summaries found for week {week} of {year}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WeeklySummarySerializer(summaries, many=True)
        return Response(serializer.data)
