"""
Content API URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DailySummaryViewSet, WeeklySummaryViewSet

router = DefaultRouter()
router.register(r"weekly-summaries", WeeklySummaryViewSet, basename="weekly-summary")
router.register(r"daily-summaries", DailySummaryViewSet, basename="daily-summary")

urlpatterns = [
    path("", include(router.urls)),
]
