"""
Django admin interface for the Job Runner.

Provides:
- JobRun changelist with auto-refresh and progress display
- Dashboard view listing available job types with "Run Now" buttons
- Run job view to trigger Celery tasks
"""

import logging

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from .models import JobRun
from .registry import JOB_REGISTRY

logger = logging.getLogger(__name__)


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "job_type_label",
        "status_display",
        "progress_display",
        "progress_detail",
        "duration_display",
        "triggered_by",
        "created_at",
    ]
    list_filter = ["status", "job_type"]
    readonly_fields = [
        "job_type",
        "celery_task_id",
        "status",
        "progress_current",
        "progress_total",
        "progress_detail",
        "result",
        "error_message",
        "items_succeeded",
        "items_failed",
        "triggered_by",
        "started_at",
        "completed_at",
        "created_at",
    ]
    ordering = ["-created_at"]

    # Custom changelist template with auto-refresh
    change_list_template = "admin/jobs/jobrun/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def job_type_label(self, obj):
        entry = JOB_REGISTRY.get(obj.job_type, {})
        return entry.get("label", obj.job_type)

    job_type_label.short_description = "Job"

    def status_display(self, obj):
        icons = {
            "pending": "\u23f3",
            "running": "\u25b6\ufe0f",
            "completed": "\u2705",
            "failed": "\u274c",
            "cancelled": "\u23f9\ufe0f",
        }
        icon = icons.get(obj.status, "")
        return f"{icon} {obj.get_status_display()}"

    status_display.short_description = "Status"

    def progress_display(self, obj):
        if obj.progress_total == 0:
            return "-"
        return f"{obj.progress_current}/{obj.progress_total} ({obj.progress_percent}%)"

    progress_display.short_description = "Progress"

    def duration_display(self, obj):
        if not obj.started_at:
            return "-"
        end = obj.completed_at or timezone.now()
        delta = end - obj.started_at
        total_seconds = int(delta.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    duration_display.short_description = "Duration"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "dashboard/",
                self.admin_site.admin_view(self.dashboard_view),
                name="jobs_dashboard",
            ),
            path(
                "run/<str:job_type>/",
                self.admin_site.admin_view(self.run_job_view),
                name="jobs_run",
            ),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        """Dashboard page listing available jobs with Run buttons."""
        jobs = []
        for key, config in JOB_REGISTRY.items():
            running = JobRun.objects.filter(
                job_type=key, status__in=["pending", "running"]
            ).first()
            last_completed = (
                JobRun.objects.filter(job_type=key, status="completed")
                .order_by("-completed_at")
                .first()
            )
            jobs.append(
                {
                    "key": key,
                    "label": config["label"],
                    "description": config["description"],
                    "queue": config["queue"],
                    "is_running": running is not None,
                    "running_job": running,
                    "last_completed": last_completed,
                }
            )

        recent_jobs = JobRun.objects.all()[:10]

        context = {
            **self.admin_site.each_context(request),
            "title": "Job Runner Dashboard",
            "jobs": jobs,
            "recent_jobs": recent_jobs,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/jobs/dashboard.html", context)

    def run_job_view(self, request, job_type):
        """Trigger a job run via POST."""
        if request.method != "POST":
            return HttpResponseRedirect(reverse("admin:jobs_dashboard"))

        config = JOB_REGISTRY.get(job_type)
        if not config:
            messages.error(request, f"Unknown job type: {job_type}")
            return HttpResponseRedirect(reverse("admin:jobs_dashboard"))

        # Prevent duplicate concurrent runs
        if JobRun.objects.filter(
            job_type=job_type, status__in=["pending", "running"]
        ).exists():
            messages.warning(request, f"{config['label']} is already running.")
            return HttpResponseRedirect(reverse("admin:jobs_dashboard"))

        # Create the JobRun record
        job_run = JobRun.objects.create(
            job_type=job_type,
            status=JobRun.Status.PENDING,
            triggered_by=request.user,
        )

        # Dispatch the Celery task
        from celery import current_app

        task = current_app.send_task(
            config["task"],
            args=[job_run.id],
            queue=config["queue"],
        )

        # Store the Celery task ID
        job_run.celery_task_id = task.id
        job_run.save(update_fields=["celery_task_id"])

        logger.info(
            f"Job #{job_run.id} ({job_type}) started by {request.user.username}"
        )
        messages.success(request, f"Started: {config['label']} (Job #{job_run.id})")
        return HttpResponseRedirect(reverse("admin:jobs_jobrun_changelist"))
