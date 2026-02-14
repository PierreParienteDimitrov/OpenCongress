"""
Job runner models for tracking Celery task execution.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class JobRun(models.Model):
    """Tracks execution of admin-triggered Celery jobs with progress."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    # Which job type (matches keys in JOB_REGISTRY)
    job_type = models.CharField(max_length=100)

    # Celery task ID for the wrapper task
    celery_task_id = models.CharField(max_length=255, blank=True)

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Progress tracking
    progress_current = models.IntegerField(default=0)
    progress_total = models.IntegerField(default=0)
    progress_detail = models.CharField(max_length=500, blank=True)

    # Accumulated log output (appended to during execution)
    log = models.TextField(blank=True, default="")

    # Results
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    items_succeeded = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)

    # Metadata
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "job_runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["job_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.job_type} - {self.status} ({self.created_at:%Y-%m-%d %H:%M})"

    @property
    def progress_percent(self):
        if self.progress_total == 0:
            return 0
        return round((self.progress_current / self.progress_total) * 100)

    @property
    def duration(self):
        if not self.started_at:
            return None
        end = self.completed_at or timezone.now()
        return end - self.started_at

    @property
    def job_type_label(self):
        from .registry import JOB_REGISTRY

        entry = JOB_REGISTRY.get(self.job_type, {})
        return entry.get("label", self.job_type)

    @property
    def duration_display(self):
        if not self.started_at:
            return "-"
        end = self.completed_at or timezone.now()
        total_seconds = int((end - self.started_at).total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
