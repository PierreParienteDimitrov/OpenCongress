"""
ViewSets for the Congress API.
"""

import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.db.models import OuterRef, Subquery
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend  # type: ignore[import-untyped]
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.congress.models import (
    Bill,
    CandidateFinance,
    CBOCostEstimate,
    Committee,
    Hearing,
    Member,
    MemberVote,
    Seat,
    Vote,
)
from apps.congress.zcta import STATE_NAMES, ZCTA_CD

from .filters import BillFilter, CommitteeFilter, MemberFilter, VoteFilter
from .search import MemberSearchFilter
from .serializers import (
    BillCalendarSerializer,
    BillDetailSerializer,
    BillListSerializer,
    CandidateFinanceDetailSerializer,
    CandidateFinanceListSerializer,
    CBOCostEstimateSerializer,
    CommitteeDetailSerializer,
    CommitteeListSerializer,
    HearingDetailSerializer,
    HearingListSerializer,
    MemberDetailSerializer,
    MemberListSerializer,
    SeatSerializer,
    SeatVoteOverlaySerializer,
    VoteCalendarSerializer,
    VoteSummarySerializer,
)

logger = logging.getLogger(__name__)


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
    filter_backends = [DjangoFilterBackend, MemberSearchFilter, OrderingFilter]
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

    @action(detail=False, methods=["get"], url_path="zip-lookup")
    def zip_lookup(self, request):
        """Look up congressional district by zip code using local ZCTA data."""
        zip_code = request.query_params.get("zip", "").strip()

        if not zip_code or not re.match(r"^\d{5}$", zip_code):
            return Response(
                {"error": "A valid 5-digit zip code is required"},
                status=400,
            )

        # Check cache first (30 days)
        cache_key = f"zip_lookup:{zip_code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        # Look up in static ZCTA → CD mapping
        entry = ZCTA_CD.get(zip_code)
        if not entry:
            return Response(
                {"error": "No results found for this zip code"},
                status=404,
            )

        state_code = entry["state"]
        districts = entry["districts"]

        # Find matching members
        members = Member.objects.filter(is_active=True, state=state_code)
        senate_members = list(members.filter(chamber=Member.Chamber.SENATE))
        house_members = list(
            members.filter(chamber=Member.Chamber.HOUSE, district__in=districts)
        )
        all_members = senate_members + house_members

        serializer = MemberListSerializer(all_members, many=True)

        # Use the first district as the primary (most zip codes have one)
        result = {
            "state": state_code,
            "state_name": STATE_NAMES.get(state_code, state_code),
            "district": districts[0] if len(districts) == 1 else None,
            "members": serializer.data,
        }

        # Cache for 30 days
        cache.set(cache_key, result, 60 * 60 * 24 * 30)

        return Response(result)


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


class CommitteeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Congressional Committees.

    list: Get all top-level committees with optional filtering
    retrieve: Get a specific committee with members, subcommittees, and bills
    """

    queryset = Committee.objects.filter(parent_committee__isnull=True).order_by(
        "chamber", "name"
    )
    filterset_class = CommitteeFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "chamber"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CommitteeDetailSerializer
        return CommitteeListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Allow search by name
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        if self.action == "retrieve":
            queryset = Committee.objects.all()  # Allow retrieving subcommittees too
            queryset = queryset.prefetch_related(
                "members__member",
                "subcommittees",
                "referred_bills__bill__sponsor",
            )
        return queryset

    @method_decorator(cache_page(settings.CACHE_TIMEOUTS.get("member_list", 60 * 60)))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(settings.CACHE_TIMEOUTS.get("member_detail", 60 * 60)))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CandidateFinanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for campaign finance data.

    list: Get finance summaries for all members
    retrieve: Get detailed finance data for a specific finance record
    by_member: Get finance data for a specific member (by bioguide_id)
    """

    queryset = CandidateFinance.objects.select_related("member").order_by(
        "-total_receipts"
    )
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["cycle", "member__chamber", "member__party", "member__state"]
    ordering_fields = [
        "total_receipts",
        "total_disbursements",
        "cash_on_hand",
        "individual_contributions",
        "pac_contributions",
    ]

    def get_serializer_class(self):
        if self.action in ("retrieve", "by_member"):
            return CandidateFinanceDetailSerializer
        return CandidateFinanceListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ("retrieve", "by_member"):
            queryset = queryset.prefetch_related(
                "top_contributors", "industry_contributions"
            )
        return queryset

    @action(detail=False, methods=["get"], url_path="member/(?P<bioguide_id>[^/.]+)")
    def by_member(self, request, bioguide_id=None):
        """Get finance data for a specific member by bioguide_id."""
        cycle = request.query_params.get("cycle")

        queryset = (
            CandidateFinance.objects.filter(member__bioguide_id=bioguide_id)
            .select_related("member")
            .prefetch_related("top_contributors", "industry_contributions")
        )

        if cycle:
            queryset = queryset.filter(cycle=cycle)

        queryset = queryset.order_by("-cycle")

        if not queryset.exists():
            return Response(
                {"error": f"No finance data found for member {bioguide_id}"},
                status=404,
            )

        serializer = CandidateFinanceDetailSerializer(queryset, many=True)
        return Response(serializer.data)


class HearingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for committee hearings and meetings.

    list: Get all hearings with optional filtering
    retrieve: Get a specific hearing with witnesses and related bills
    upcoming: Get upcoming scheduled hearings
    """

    queryset = Hearing.objects.select_related("committee").order_by("-date")
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
        "chamber",
        "meeting_type",
        "meeting_status",
        "congress",
        "committee__committee_id",
    ]
    ordering_fields = ["date", "chamber", "meeting_type"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return HearingDetailSerializer
        return HearingListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("witnesses", "related_bills__sponsor")

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming scheduled hearings."""
        from django.utils import timezone

        queryset = (
            Hearing.objects.filter(
                date__gte=timezone.now(),
                meeting_status="scheduled",
            )
            .select_related("committee")
            .order_by("date")[:50]
        )
        serializer = HearingListSerializer(queryset, many=True)
        return Response(serializer.data)


class CBOCostEstimateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for CBO cost estimates.

    list: Get all CBO cost estimates
    retrieve: Get a specific CBO cost estimate
    for_bill: Get CBO estimates for a specific bill
    """

    queryset = CBOCostEstimate.objects.select_related("bill").order_by(
        "-publication_date"
    )
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["congress", "bill__bill_id"]
    ordering_fields = ["publication_date", "congress"]
    serializer_class = CBOCostEstimateSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path="bill/(?P<bill_id>[^/.]+)",
    )
    def for_bill(self, request, bill_id=None):
        """Get CBO cost estimates for a specific bill."""
        queryset = (
            CBOCostEstimate.objects.filter(bill__bill_id=bill_id)
            .select_related("bill")
            .order_by("-publication_date")
        )

        if not queryset.exists():
            return Response(
                {"error": f"No CBO estimates found for bill {bill_id}"},
                status=404,
            )

        serializer = CBOCostEstimateSerializer(queryset, many=True)
        return Response(serializer.data)
