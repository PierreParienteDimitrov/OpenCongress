"""
AI-generated content models for CongressTrack.
"""

from django.db import models


class AISummary(models.Model):
    """Stores AI-generated summaries for various content types."""

    class ContentType(models.TextChoices):
        BILL = "bill", "Bill"
        VOTE = "vote", "Vote"
        MEMBER = "member", "Member"

    id = models.BigAutoField(primary_key=True)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    content_id = models.CharField(max_length=50)

    summary_text = models.TextField()
    model_used = models.CharField(max_length=50)
    prompt_version = models.CharField(max_length=20)
    tokens_used = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_summaries"
        unique_together = ("content_type", "content_id")


class TrendReport(models.Model):
    """Weekly/monthly trend analysis reports."""

    class ReportType(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    id = models.BigAutoField(primary_key=True)
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    period_start = models.DateField()
    period_end = models.DateField()

    data = models.JSONField()
    summary_text = models.TextField()

    model_used = models.CharField(max_length=50)
    prompt_version = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trend_reports"
        indexes = [
            models.Index(fields=["report_type", "period_start"]),
        ]


class NewsLink(models.Model):
    """News articles related to bills or votes."""

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=500)
    url = models.URLField()
    source = models.CharField(max_length=200)
    published_at = models.DateTimeField()

    # Can be linked to a bill or vote
    bill_id = models.CharField(max_length=50, blank=True)
    vote_id = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "news_links"
        indexes = [
            models.Index(fields=["bill_id"]),
            models.Index(fields=["vote_id"]),
        ]
