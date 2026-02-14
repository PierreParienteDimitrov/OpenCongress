from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    APIKeyCreateUpdateView,
    APIKeyDeleteView,
    APIKeyListView,
    FollowMemberView,
    MeView,
    MyRepresentativesView,
    SocialAuthSyncView,
    chat_stream_view,
)

urlpatterns = [
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("social-sync/", SocialAuthSyncView.as_view(), name="social_auth_sync"),
    # API key management
    path("api-keys/", APIKeyListView.as_view(), name="api_keys_list"),
    path("api-keys/create/", APIKeyCreateUpdateView.as_view(), name="api_keys_create"),
    path(
        "api-keys/<str:provider>/delete/",
        APIKeyDeleteView.as_view(),
        name="api_keys_delete",
    ),
    # Representatives
    path(
        "my-representatives/",
        MyRepresentativesView.as_view(),
        name="my_representatives",
    ),
    path(
        "follow/<str:bioguide_id>/",
        FollowMemberView.as_view(),
        name="follow_member",
    ),
    # Chat
    path("chat/stream/", chat_stream_view, name="chat_stream"),
]
