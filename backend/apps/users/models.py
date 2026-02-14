"""
User models for CongressTrack.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model for CongressTrack."""

    # Address/location for finding representatives
    address = models.TextField(blank=True)
    zip_code = models.CharField(max_length=5, blank=True)
    state = models.CharField(max_length=2, blank=True)
    congressional_district = models.CharField(max_length=10, blank=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = "user"
        verbose_name_plural = "users"


class UserAPIKey(models.Model):
    """Stores encrypted AI provider API keys for users."""

    PROVIDER_CHOICES = [
        ("anthropic", "Anthropic (Claude)"),
        ("openai", "OpenAI (GPT)"),
        ("google", "Google (Gemini)"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    encrypted_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_api_keys"
        unique_together = ("user", "provider")
        ordering = ["-created_at"]

    def set_key(self, plain_key: str):
        """Encrypt and store an API key."""
        from services.encryption import EncryptionService

        self.encrypted_key = EncryptionService().encrypt(plain_key)

    def get_key(self) -> str:
        """Decrypt and return the API key."""
        from services.encryption import EncryptionService

        return EncryptionService().decrypt(self.encrypted_key)


class UserFollow(models.Model):
    """Tracks which Congress members a user follows."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follows",
    )
    bioguide_id = models.CharField(max_length=10)  # Reference to Member
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_follows"
        unique_together = ("user", "bioguide_id")


class BillTrack(models.Model):
    """Tracks which bills a user is tracking."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tracked_bills",
    )
    bill_id = models.CharField(max_length=50)  # Reference to Bill
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bill_tracks"
        unique_together = ("user", "bill_id")
