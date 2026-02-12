"""
ViewSets for the Congress API.
"""

from django.conf import settings
from django.db.models import OuterRef, Subquery
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.congress.models import Bill, Member, MemberVote, Seat, Vote

from .filters import BillFilter, MemberFilter, VoteFilter
from .serializers import (
    BillCalendarSerializer,
    BillDetailSerializer,
    BillListSerializer,
    MemberDetailSerializer,
    MemberListSerializer,
    SeatSerializer,
    SeatVoteOverlaySerializer,
    VoteCalendarSerializer,
    VoteSummarySerializer,
)


class MemberViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Congress members.

    list: Get all members with optional filtering
    retrieve: Get a specific member by bioguide_id
    representatives: Get all House members
    senators: Get all Senate members
    """

    queryset = Member.objects.filter(is_active=True).order_by("last_name", "first_name")
    filterset_class = MemberFilter
    search_fields = ["full_name", "last_name", "first_name", "state"]
    ordering_fields = ["full_name", "last_name", "state", "party"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MemberDetailSerializer
        return MemberListSerializer

    @method_decorator(cache_page(settings.CACHE_TIMEOUTS.get("member_list", 60 * 60)))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(settings.CACHE_TIMEOUTS.get("member_detail", 60 * 60)))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    @method_decorator(
        cache_page(settings.CACHE_TIMEOUTS.get("representatives", 60 * 60 * 24))
    )
    def representatives(self, request):
        """Get all House of Representatives members."""
        queryset = self.filter_queryset(
            self.get_queryset().filter(chamber=Member.Chamber.HOUSE)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MemberListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MemberListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(settings.CACHE_TIMEOUTS.get("member_list", 60 * 60)))
    def senators(self, request):
        """Get all Senate members."""
        queryset = self.filter_queryset(
            self.get_queryset().filter(chamber=Member.Chamber.SENATE)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MemberListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MemberListSerializer(queryset, many=True)
        return Response(serializer.data)


class BillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Bills.

    list: Get all bills with optional filtering
    retrieve: Get a specific bill by bill_id with votes
    calendar: Get bills by action date range (for calendar view)
    """

    queryset = Bill.objects.select_related("sponsor").order_by("-latest_action_date")
    filterset_class = BillFilter
    search_fields = ["title", "short_title", "display_number"]
    ordering_fields = ["introduced_date", "latest_action_date", "display_number"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BillDetailSerializer
        if self.action == "calendar":
            return BillCalendarSerializer
        return BillListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("votes")
        return queryset

    @method_decorator(
        cache_page(settings.CACHE_TIMEOUTS.get("vote_detail", 60 * 60 * 24))
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        """
        Get bills with activity in a date range.

        Query params:
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        queryset = self.get_queryset()

        if date_from:
            queryset = queryset.filter(latest_action_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(latest_action_date__lte=date_to)

        queryset = queryset.order_by("latest_action_date")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Votes.

    list: Get all votes with optional filtering
    retrieve: Get a specific vote by vote_id
    calendar: Get votes by date range (for calendar view)
    """

    queryset = Vote.objects.select_related("bill").order_by("-date", "-time")
    filterset_class = VoteFilter
    search_fields = ["question", "description"]
    ordering_fields = ["date", "chamber", "result"]

    def get_serializer_class(self):
        if self.action == "calendar":
            return VoteCalendarSerializer
        return VoteSummarySerializer

    @method_decorator(cache_page(settings.CACHE_TIMEOUTS.get("vote_list", 60 * 5)))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(
        cache_page(settings.CACHE_TIMEOUTS.get("vote_detail", 60 * 60 * 24))
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        """
        Get votes in a date range.

        Query params:
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        queryset = self.get_queryset()

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        queryset = queryset.order_by("date", "time")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for hemicycle seat data.

    list: Get all seats for a chamber with member info (party-colored view).
          Query params: chamber (required: "house" or "senate")
    vote_overlay: Get all seats annotated with vote positions for a specific vote.
          Query params: chamber (required), vote_id (required)
    """

    queryset = Seat.objects.select_related("member").order_by("row", "position")
    serializer_class = SeatSerializer
    pagination_class = None  # Return all seats at once (max 435)

    def get_queryset(self):
        queryset = super().get_queryset()
        chamber = self.request.query_params.get("chamber")
        if chamber in ("house", "senate"):
            queryset = queryset.filter(chamber=chamber)
        return queryset

    @method_decorator(
        cache_page(settings.CACHE_TIMEOUTS.get("hemicycle", 60 * 60 * 24))
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="vote-overlay")
    def vote_overlay(self, request):
        """Get seats with vote overlay for a specific vote."""
        chamber = request.query_params.get("chamber")
        vote_id = request.query_params.get("vote_id")

        if not chamber or chamber not in ("house", "senate"):
            return Response(
                {"error": "chamber parameter is required (house or senate)"},
                status=400,
            )
        if not vote_id:
            return Response(
                {"error": "vote_id parameter is required"},
                status=400,
            )

        vote_position_subquery = Subquery(
            MemberVote.objects.filter(
                vote_id=vote_id,
                member_id=OuterRef("member_id"),
            ).values("position")[:1]
        )

        queryset = (
            Seat.objects.filter(chamber=chamber)
            .select_related("member")
            .annotate(vote_position=vote_position_subquery)
            .order_by("row", "position")
        )

        serializer = SeatVoteOverlaySerializer(queryset, many=True)
        return Response(serializer.data)
