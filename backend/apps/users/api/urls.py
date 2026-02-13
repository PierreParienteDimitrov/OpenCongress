from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import MeView, SocialAuthSyncView

urlpatterns = [
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("social-sync/", SocialAuthSyncView.as_view(), name="social_auth_sync"),
]
