"""
Core URL patterns including health checks.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("ready/", views.ready_check, name="ready_check"),
]
