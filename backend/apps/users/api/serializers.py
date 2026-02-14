from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "state",
            "congressional_district",
            "email_notifications",
            "push_notifications",
            "created_at",
        ]
        read_only_fields = ["id", "username", "email", "created_at"]


class APIKeyCreateSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["anthropic", "openai", "google"])
    api_key = serializers.CharField(min_length=10, max_length=500, write_only=True)

    def validate_api_key(self, value):
        return value.strip()


class APIKeyListSerializer(serializers.ModelSerializer):
    provider_display = serializers.CharField(
        source="get_provider_display", read_only=True
    )

    class Meta:
        from apps.users.models import UserAPIKey

        model = UserAPIKey
        fields = ["id", "provider", "provider_display", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SocialAuthSerializer(serializers.Serializer):
    provider = serializers.CharField()
    provider_account_id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField(required=False, allow_blank=True, default="")
    image = serializers.URLField(required=False, allow_blank=True, default="")
