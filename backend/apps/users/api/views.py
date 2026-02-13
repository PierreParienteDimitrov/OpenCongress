import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import SocialAuthSerializer, UserSerializer

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
            return Response(
                {"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN
            )

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
