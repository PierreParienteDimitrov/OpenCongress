"""
URL configuration for the Congress API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BillViewSet,
    CandidateFinanceViewSet,
    CBOCostEstimateViewSet,
    CommitteeViewSet,
    HearingViewSet,
    MemberViewSet,
    SeatViewSet,
    VoteViewSet,
)

router = DefaultRouter()
router.register("members", MemberViewSet, basename="member")
router.register("bills", BillViewSet, basename="bill")
router.register("votes", VoteViewSet, basename="vote")
router.register("seats", SeatViewSet, basename="seat")
router.register("committees", CommitteeViewSet, basename="committee")
router.register("finance", CandidateFinanceViewSet, basename="finance")
router.register("hearings", HearingViewSet, basename="hearing")
router.register("cbo-estimates", CBOCostEstimateViewSet, basename="cbo-estimate")

urlpatterns = [
    path("", include(router.urls)),
]
