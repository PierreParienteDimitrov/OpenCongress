import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.http import StreamingHttpResponse
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import UserAPIKey
from services.chat import ChatService

from .serializers import (
    APIKeyCreateSerializer,
    APIKeyListSerializer,
    SocialAuthSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class MeView(generics.RetrieveUpdateAPIView):
    """Get or update the current user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SocialAuthSyncView(APIView):
    """
    Sync a social login user to Django.

    Called server-to-server by Auth.js after a successful OAuth login.
    Secured via a shared secret in the X-Auth-Sync-Secret header.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        sync_secret = request.headers.get("X-Auth-Sync-Secret")
        expected = getattr(settings, "AUTH_SYNC_SECRET", None)
        if not expected or sync_secret != expected:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data["email"].lower()

        # Try to find existing user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user, handling potential username collision
            base_username = email.split("@")[0]
            username = base_username
            for _ in range(5):
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                    )
                    break
                except IntegrityError:
                    username = f"{base_username}_{uuid.uuid4().hex[:6]}"
            else:
                return Response(
                    {"error": "Could not create user"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


class APIKeyListView(generics.ListAPIView):
    """List configured API key providers for the current user (no key values)."""

    serializer_class = APIKeyListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return UserAPIKey.objects.filter(user=self.request.user)


class APIKeyCreateUpdateView(APIView):
    """Create or update an encrypted API key for a provider."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        api_key = serializer.validated_data["api_key"]

        key_obj, created = UserAPIKey.objects.get_or_create(
            user=request.user,
            provider=provider,
        )
        key_obj.set_key(api_key)
        key_obj.save()

        return Response(
            {"provider": provider, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class APIKeyDeleteView(APIView):
    """Delete an API key for a provider."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, provider):
        deleted, _ = UserAPIKey.objects.filter(
            user=request.user, provider=provider
        ).delete()
        if not deleted:
            return Response(
                {"error": "API key not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Chat streaming
# ---------------------------------------------------------------------------

VALID_PROVIDERS = {"anthropic", "openai", "google"}


class ChatRateThrottle(UserRateThrottle):
    rate = "30/hour"


def _build_system_context(page_context: dict) -> str:
    """Build a system prompt from page context."""
    base = (
        "You are an AI assistant for OpenCongress, a non-partisan platform for "
        "tracking U.S. legislative activity. Help users understand congressional "
        "bills, votes, and members. Be concise, factual, and non-partisan. "
        "When discussing legislation, include bill numbers. "
        "When you don't know something, say so."
    )

    ctx_type = page_context.get("type", "")
    data = page_context.get("data", {})

    if ctx_type == "bill":
        return (
            f"{base}\n\n"
            f"The user is viewing a bill.\n"
            f"Bill: {data.get('display_number', 'N/A')}\n"
            f"Title: {data.get('title', 'N/A')}\n"
            f"Sponsor: {data.get('sponsor_name', 'N/A')}\n"
            f"Latest action: {data.get('latest_action', 'N/A')}\n"
            f"Summary: {str(data.get('summary', 'N/A'))[:800]}"
        )
    elif ctx_type == "vote":
        return (
            f"{base}\n\n"
            f"The user is viewing a vote.\n"
            f"Vote ID: {data.get('vote_id', 'N/A')}\n"
            f"Question: {data.get('question', 'N/A')}\n"
            f"Result: {data.get('result', 'N/A')}\n"
            f"Date: {data.get('date', 'N/A')}\n"
            f"Yea: {data.get('total_yea', 'N/A')} / "
            f"Nay: {data.get('total_nay', 'N/A')}"
        )
    elif ctx_type == "member":
        return (
            f"{base}\n\n"
            f"The user is viewing a member profile.\n"
            f"Name: {data.get('full_name', 'N/A')}\n"
            f"Party: {data.get('party', 'N/A')}\n"
            f"State: {data.get('state', 'N/A')}\n"
            f"Chamber: {data.get('chamber', 'N/A')}"
        )
    elif ctx_type == "chamber":
        return (
            f"{base}\n\n"
            f"The user is viewing the {data.get('chamber', '')} chamber page."
        )
    elif ctx_type == "calendar":
        return f"{base}\n\nThe user is viewing the legislative calendar."
    elif ctx_type == "this-week":
        return (
            f"{base}\n\n"
            f"The user is viewing the weekly summary page.\n"
            f"Summary: {str(data.get('summary', ''))[:800]}"
        )
    else:
        return base


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([ChatRateThrottle])
def chat_stream_view(request):
    """
    Stream a chat response via SSE.

    POST body:
        provider: "anthropic" | "openai" | "google"
        messages: [{"role": "user"|"assistant", "content": "..."}]
        page_context: {"type": "...", "data": {...}}
    """
    provider = request.data.get("provider")
    messages = request.data.get("messages", [])
    page_context = request.data.get("page_context", {})

    if provider not in VALID_PROVIDERS:
        return StreamingHttpResponse(
            iter([_sse_event({"error": "Invalid provider"})]),
            content_type="text/event-stream",
            status=400,
        )

    if not messages:
        return StreamingHttpResponse(
            iter([_sse_event({"error": "No messages provided"})]),
            content_type="text/event-stream",
            status=400,
        )

    try:
        key_obj = UserAPIKey.objects.get(user=request.user, provider=provider)
        api_key = key_obj.get_key()
    except UserAPIKey.DoesNotExist:
        return StreamingHttpResponse(
            iter([_sse_event({"error": "No API key configured for this provider"})]),
            content_type="text/event-stream",
            status=400,
        )

    system_context = _build_system_context(page_context)

    def event_stream():
        try:
            service = ChatService(provider, api_key)
            for chunk in service.stream_chat(messages, system_context):
                yield _sse_event({"chunk": chunk})
            yield _sse_event({"done": True})
        except Exception as e:
            logger.error("Chat streaming error for user %s: %s", request.user.id, e)
            yield _sse_event({"error": str(e)})

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
