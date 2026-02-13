"""
ViewSets for the Congress API.
"""

import logging
import re

import requests
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

from apps.congress.models import Bill, Member, MemberVote, Seat, Vote

from .filters import BillFilter, MemberFilter, VoteFilter
from .search import MemberSearchFilter
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

logger = logging.getLogger(__name__)

# FIPS → state postal code mapping for zip lookup
FIPS_TO_STATE: dict[str, str] = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    "60": "AS",
    "66": "GU",
    "69": "MP",
    "72": "PR",
    "78": "VI",
}

STATE_NAMES: dict[str, str] = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "AS": "American Samoa",
    "GU": "Guam",
    "MP": "Northern Mariana Islands",
    "PR": "Puerto Rico",
    "VI": "U.S. Virgin Islands",
}


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
        """Look up congressional district by zip code using Census Geocoder API."""
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

        # Call Census Geocoder API
        census_url = "https://geocoding.geo.census.gov/geocoder/geographies/address"
        params = {
            "street": "",
            "city": "",
            "state": "",
            "zip": zip_code,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json",
        }

        try:
            resp = requests.get(census_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.exception("Census Geocoder API call failed for zip=%s", zip_code)
            return Response(
                {"error": "Failed to look up zip code"},
                status=502,
            )

        # Parse response for congressional district info
        matches = data.get("result", {}).get("addressMatches", [])
        if not matches:
            return Response(
                {"error": "No results found for this zip code"},
                status=404,
            )

        # Get geographic data from first match
        geographies = matches[0].get("geographies", {})
        cd_list = geographies.get("119th Congressional Districts", [])

        if not cd_list:
            return Response(
                {"error": "No congressional district found for this zip code"},
                status=404,
            )

        cd_info = cd_list[0]
        state_fips = cd_info.get("STATE", "")
        district_str = cd_info.get("CD119", "00")

        state_code = FIPS_TO_STATE.get(state_fips)
        if not state_code:
            return Response(
                {"error": "Could not resolve state for this zip code"},
                status=404,
            )

        district_num = int(district_str) if district_str else 0

        # Find matching members
        members = Member.objects.filter(is_active=True, state=state_code)
        # For house members, filter by district; for senators, include all
        house_members = list(
            members.filter(chamber=Member.Chamber.HOUSE, district=district_num)
        )
        senate_members = list(members.filter(chamber=Member.Chamber.SENATE))
        all_members = senate_members + house_members

        serializer = MemberListSerializer(all_members, many=True)

        result = {
            "state": state_code,
            "state_name": STATE_NAMES.get(state_code, state_code),
            "district": district_num,
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
