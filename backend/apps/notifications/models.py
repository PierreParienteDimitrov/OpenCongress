"""
Notification models for CongressTrack.
"""

from django.db import models

from apps.users.models import User


class Notification(models.Model):
    """User notifications for votes, bill updates, etc."""

    class NotificationType(models.TextChoices):
        VOTE = "vote", "New Vote"
        BILL_UPDATE = "bill_update", "Bill Update"
        WEEKLY_RECAP = "weekly_recap", "Weekly Recap"
        WEEKLY_FORECAST = "weekly_forecast", "Weekly Forecast"

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]


class EmailLog(models.Model):
    """Log of sent emails."""

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_logs",
    )
    subject = models.CharField(max_length=500)
    template_name = models.CharField(max_length=100)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="sent")

    class Meta:
        db_table = "email_logs"
