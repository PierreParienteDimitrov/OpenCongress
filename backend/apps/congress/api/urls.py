"""
URL configuration for the Congress API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BillViewSet, MemberViewSet, VoteViewSet

router = DefaultRouter()
router.register("members", MemberViewSet, basename="member")
router.register("bills", BillViewSet, basename="bill")
router.register("votes", VoteViewSet, basename="vote")

urlpatterns = [
    path("", include(router.urls)),
]
