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
from django.utils.html import format_html

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
        "duration_col",
        "triggered_by",
        "created_at",
        "actions_display",
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

    # Custom templates
    change_list_template = "admin/jobs/jobrun/change_list.html"
    change_form_template = "admin/jobs/jobrun/change_form.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Job")
    def job_type_label(self, obj):
        return obj.job_type_label

    @admin.display(description="Status")
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

    @admin.display(description="Progress")
    def progress_display(self, obj):
        if obj.progress_total == 0:
            return "-"
        return f"{obj.progress_current}/{obj.progress_total} ({obj.progress_percent}%)"

    @admin.display(description="Duration")
    def duration_col(self, obj):
        return obj.duration_display

    @admin.display(description="")
    def actions_display(self, obj):
        if obj.status in ("pending", "running"):
            stop_url = reverse("admin:jobs_stop", args=[obj.id])
            return format_html(
                '<form method="post" action="{}" class="stop-job-form"'
                ' style="display:inline">'
                '<button type="submit" style="background:#dc3545;color:#fff;'
                "border:none;padding:4px 12px;border-radius:4px;cursor:pointer;"
                'font-size:0.8rem">'
                "\u23f9 Stop</button></form>",
                stop_url,
            )
        return ""

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
            path(
                "stop/<int:job_run_id>/",
                self.admin_site.admin_view(self.stop_job_view),
                name="jobs_stop",
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
        return HttpResponseRedirect(
            request.META.get("HTTP_REFERER", reverse("admin:jobs_jobrun_changelist"))
        )

    def stop_job_view(self, request, job_run_id):
        """Stop a running job by revoking the Celery task."""
        if request.method != "POST":
            return HttpResponseRedirect(reverse("admin:jobs_dashboard"))

        try:
            job_run = JobRun.objects.get(id=job_run_id)
        except JobRun.DoesNotExist:
            messages.error(request, f"Job run #{job_run_id} not found.")
            return HttpResponseRedirect(reverse("admin:jobs_dashboard"))

        if job_run.status not in ("pending", "running"):
            messages.warning(
                request, f"Job #{job_run_id} is not running (status: {job_run.status})."
            )
            return HttpResponseRedirect(reverse("admin:jobs_dashboard"))

        # Revoke the Celery task
        if job_run.celery_task_id:
            from celery import current_app

            current_app.control.revoke(
                job_run.celery_task_id, terminate=True, signal="SIGTERM"
            )
            logger.info(
                f"Revoked Celery task {job_run.celery_task_id} for job #{job_run_id}"
            )

        # Update the JobRun record
        job_run.status = JobRun.Status.CANCELLED
        job_run.completed_at = timezone.now()
        job_run.progress_detail = f"Stopped by {request.user.username}"
        job_run.save(update_fields=["status", "completed_at", "progress_detail"])

        entry = JOB_REGISTRY.get(job_run.job_type, {})
        label = entry.get("label", job_run.job_type)
        logger.info(
            f"Job #{job_run_id} ({job_run.job_type}) stopped by {request.user.username}"
        )
        messages.success(request, f"Stopped: {label} (Job #{job_run_id})")
        return HttpResponseRedirect(
            request.META.get("HTTP_REFERER", reverse("admin:jobs_dashboard"))
        )
