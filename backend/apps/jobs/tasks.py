"""
Job runner wrapper tasks.

These tasks wrap the existing single-item tasks (generate_member_bio, etc.)
and run them sequentially with progress tracking via the JobRun model.
"""

import logging
import traceback

from celery import shared_task
from celery.exceptions import Retry as CeleryRetry
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Progress helpers — all use single UPDATE queries, no full model load
# ---------------------------------------------------------------------------


def _start_job(job_run_id, total):
    """Mark job as running with known total."""
    from apps.jobs.models import JobRun

    JobRun.objects.filter(id=job_run_id).update(
        status=JobRun.Status.RUNNING,
        started_at=timezone.now(),
        progress_total=total,
        progress_current=0,
        log="",
    )


def _append_log(job_run_id, line):
    """Append a line to the accumulated log field (atomic SQL concat)."""
    from apps.jobs.models import JobRun
    from django.db.models import Value
    from django.db.models.functions import Concat

    if not line:
        return
    JobRun.objects.filter(id=job_run_id).update(log=Concat("log", Value(line + "\n")))


def _update_progress(job_run_id, current, detail=""):
    """Update progress fields and append detail to accumulated log."""
    from apps.jobs.models import JobRun

    JobRun.objects.filter(id=job_run_id).update(
        progress_current=current,
        progress_detail=detail,
    )
    if detail:
        _append_log(job_run_id, detail)


def _complete_job(job_run_id, succeeded, failed, result=None):
    """Mark job as completed (even with partial failures)."""
    from apps.jobs.models import JobRun

    JobRun.objects.filter(id=job_run_id).update(
        status=JobRun.Status.COMPLETED,
        completed_at=timezone.now(),
        items_succeeded=succeeded,
        items_failed=failed,
        result=result or {},
        progress_detail=f"Done: {succeeded} succeeded, {failed} failed",
    )


def _fail_job(job_run_id, error_message):
    """Mark job as failed due to unexpected wrapper-level error."""
    from apps.jobs.models import JobRun

    JobRun.objects.filter(id=job_run_id).update(
        status=JobRun.Status.FAILED,
        completed_at=timezone.now(),
        error_message=error_message[:2000],
    )


# ---------------------------------------------------------------------------
# AI batch wrapper tasks
# ---------------------------------------------------------------------------


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_generate_member_bios(self, job_run_id: int):
    """Generate bios for ALL members needing them (no 50-item cap)."""
    from apps.congress.models import Member
    from prompts import MEMBER_BIO_VERSION
    from tasks.ai import generate_member_bio

    try:
        members = list(
            Member.objects.filter(is_active=True)
            .filter(Q(ai_bio="") | ~Q(ai_bio_prompt_version=MEMBER_BIO_VERSION))
            .values_list("bioguide_id", "full_name")
        )

        _start_job(job_run_id, len(members))

        if not members:
            _complete_job(job_run_id, 0, 0, {"message": "No members need bios"})
            return

        succeeded = 0
        failed = 0
        errors = []

        for i, (bioguide_id, full_name) in enumerate(members, 1):
            _update_progress(
                job_run_id, i - 1, f"[{i}/{len(members)}] Generating bio: {full_name}"
            )
            try:
                result = generate_member_bio(bioguide_id)
                if result.get("success"):
                    succeeded += 1
                else:
                    failed += 1
                    errors.append(
                        {"id": bioguide_id, "error": result.get("error", "Unknown")}
                    )
            except CeleryRetry:
                failed += 1
                errors.append({"id": bioguide_id, "error": "Task failed after retries"})
            except Exception as e:
                failed += 1
                errors.append({"id": bioguide_id, "error": str(e)})
                logger.error(f"Job {job_run_id}: error on {bioguide_id}: {e}")

            _update_progress(job_run_id, i, f"Done: {full_name}")

        _complete_job(job_run_id, succeeded, failed, {"errors": errors[:50]})

    except Exception as e:
        logger.error(f"Job {job_run_id} crashed: {e}\n{traceback.format_exc()}")
        _fail_job(job_run_id, str(e))


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_generate_bill_summaries(self, job_run_id: int):
    """Generate summaries for ALL bills needing them."""
    from apps.congress.models import Bill
    from prompts import BILL_SUMMARY_VERSION
    from tasks.ai import generate_bill_summary

    try:
        bills = list(
            Bill.objects.filter(
                Q(ai_summary="") | ~Q(ai_summary_prompt_version=BILL_SUMMARY_VERSION)
            ).values_list("bill_id", "display_number")
        )

        _start_job(job_run_id, len(bills))

        if not bills:
            _complete_job(job_run_id, 0, 0, {"message": "No bills need summaries"})
            return

        succeeded = 0
        failed = 0
        errors = []

        for i, (bill_id, display_number) in enumerate(bills, 1):
            _update_progress(
                job_run_id,
                i - 1,
                f"[{i}/{len(bills)}] Summarizing: {display_number}",
            )
            try:
                result = generate_bill_summary(bill_id)
                if result.get("success"):
                    succeeded += 1
                else:
                    failed += 1
                    errors.append(
                        {"id": bill_id, "error": result.get("error", "Unknown")}
                    )
            except CeleryRetry:
                failed += 1
                errors.append({"id": bill_id, "error": "Task failed after retries"})
            except Exception as e:
                failed += 1
                errors.append({"id": bill_id, "error": str(e)})
                logger.error(f"Job {job_run_id}: error on {bill_id}: {e}")

            _update_progress(job_run_id, i, f"Done: {display_number}")

        _complete_job(job_run_id, succeeded, failed, {"errors": errors[:50]})

    except Exception as e:
        logger.error(f"Job {job_run_id} crashed: {e}\n{traceback.format_exc()}")
        _fail_job(job_run_id, str(e))


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_generate_vote_summaries(self, job_run_id: int):
    """Generate summaries for ALL votes needing them."""
    from apps.congress.models import Vote
    from prompts import VOTE_SUMMARY_VERSION
    from tasks.ai import generate_vote_summary

    try:
        votes = list(
            Vote.objects.filter(
                Q(ai_summary="") | ~Q(ai_summary_prompt_version=VOTE_SUMMARY_VERSION)
            ).values_list("vote_id", "description")
        )

        _start_job(job_run_id, len(votes))

        if not votes:
            _complete_job(job_run_id, 0, 0, {"message": "No votes need summaries"})
            return

        succeeded = 0
        failed = 0
        errors = []

        for i, (vote_id, description) in enumerate(votes, 1):
            _update_progress(
                job_run_id,
                i - 1,
                f"[{i}/{len(votes)}] Summarizing: {description[:60]}",
            )
            try:
                result = generate_vote_summary(vote_id)
                if result.get("success"):
                    succeeded += 1
                else:
                    failed += 1
                    errors.append(
                        {"id": vote_id, "error": result.get("error", "Unknown")}
                    )
            except CeleryRetry:
                failed += 1
                errors.append({"id": vote_id, "error": "Task failed after retries"})
            except Exception as e:
                failed += 1
                errors.append({"id": vote_id, "error": str(e)})
                logger.error(f"Job {job_run_id}: error on {vote_id}: {e}")

            _update_progress(job_run_id, i, f"Done: {description[:60]}")

        _complete_job(job_run_id, succeeded, failed, {"errors": errors[:50]})

    except Exception as e:
        logger.error(f"Job {job_run_id} crashed: {e}\n{traceback.format_exc()}")
        _fail_job(job_run_id, str(e))


# ---------------------------------------------------------------------------
# Sync wrapper tasks
# ---------------------------------------------------------------------------


@shared_task(bind=True, time_limit=600, soft_time_limit=550)
def run_sync_members(self, job_run_id: int):
    """Wrapper for sync_members — single invocation, not batch."""
    from tasks.sync import sync_members

    try:
        _start_job(job_run_id, 1)
        _update_progress(job_run_id, 0, "Syncing members from Congress.gov...")

        result = sync_members()

        if result.get("success", True):
            _update_progress(job_run_id, 1, "Sync complete")
            _complete_job(job_run_id, 1, 0, result)
        else:
            _fail_job(job_run_id, result.get("error", "Unknown error"))

    except CeleryRetry:
        _fail_job(job_run_id, "Sync task failed after retries")
    except Exception as e:
        logger.error(f"Job {job_run_id} crashed: {e}\n{traceback.format_exc()}")
        _fail_job(job_run_id, str(e))


@shared_task(bind=True, time_limit=600, soft_time_limit=550)
def run_sync_recent_votes(self, job_run_id: int):
    """Wrapper for sync_recent_votes — single invocation."""
    from tasks.sync import sync_recent_votes

    try:
        _start_job(job_run_id, 1)
        _update_progress(
            job_run_id, 0, "Syncing votes from Congress.gov + Senate.gov..."
        )

        result = sync_recent_votes()

        if result.get("success", True):
            _update_progress(job_run_id, 1, "Sync complete")
            _complete_job(job_run_id, 1, 0, result)
        else:
            _fail_job(job_run_id, result.get("error", "Unknown error"))

    except CeleryRetry:
        _fail_job(job_run_id, "Sync task failed after retries")
    except Exception as e:
        logger.error(f"Job {job_run_id} crashed: {e}\n{traceback.format_exc()}")
        _fail_job(job_run_id, str(e))


# ---------------------------------------------------------------------------
# Seed command wrapper tasks (management commands run via call_command)
# ---------------------------------------------------------------------------


class _StreamingJobWriter:
    """A file-like writer that updates JobRun.progress_detail on every write.

    Parses "Processed N …" lines from management command output to update
    progress_current so the progress bar reflects real work done.
    """

    _PROCESSED_RE = None  # compiled lazily

    def __init__(self, job_run_id: int):
        self._job_run_id = job_run_id
        self._buffer: list[str] = []
        self._current = 0

    @classmethod
    def _get_pattern(cls):
        if cls._PROCESSED_RE is None:
            import re

            cls._PROCESSED_RE = re.compile(r"Processed\s+(\d+)\s+", re.IGNORECASE)
        return cls._PROCESSED_RE

    def write(self, text: str) -> int:
        if not text or text == "\n":
            return len(text) if text else 0
        clean = text.strip()
        if clean:
            self._buffer.append(clean)
            # Try to extract a count from lines like "Processed 150 HR bills..."
            m = self._get_pattern().search(clean)
            if m:
                self._current = max(self._current, int(m.group(1)))
            _update_progress(self._job_run_id, self._current, clean)
        return len(text)

    def flush(self) -> None:
        pass

    def getvalue(self) -> str:
        return "\n".join(self._buffer)


def _run_management_command(
    job_run_id, command_name, detail_msg, progress_total=0, **kwargs
):
    """Generic helper to run a Django management command as a job."""
    import io

    from django.core.management import call_command

    try:
        _start_job(job_run_id, progress_total)
        _update_progress(job_run_id, 0, detail_msg)

        stdout = _StreamingJobWriter(job_run_id)
        stderr = io.StringIO()
        call_command(command_name, stdout=stdout, stderr=stderr, **kwargs)

        output = stdout.getvalue()
        errors = stderr.getvalue()

        # Use the final count parsed from stdout (or at least 1)
        final_count = stdout._current or 1
        _update_progress(job_run_id, final_count, "Complete")
        _complete_job(
            job_run_id,
            final_count,
            0,
            {"stdout": output[-2000:], "stderr": errors[-2000:] if errors else ""},
        )

    except Exception as e:
        logger.error(f"Job {job_run_id} crashed: {e}\n{traceback.format_exc()}")
        _fail_job(job_run_id, str(e))


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_seed_bills(self, job_run_id: int):
    """Seed HR and S bills for Congress 119 (up to 5000)."""
    _run_management_command(
        job_run_id,
        "seed_bills",
        "Seeding bills from Congress.gov...",
        progress_total=5000,
        congress=119,
        limit=5000,
        skip_existing=True,
    )


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_seed_votes(self, job_run_id: int):
    """Seed House and Senate votes for Congress 119."""
    _run_management_command(
        job_run_id,
        "seed_votes",
        "Seeding votes from Congress.gov...",
        progress_total=2000,
        congress=119,
        limit=2000,
        chamber="both",
    )


@shared_task(bind=True, time_limit=3600, soft_time_limit=3400)
def run_seed_senate_votes(self, job_run_id: int):
    """Seed Senate votes from Senate.gov XML."""
    _run_management_command(
        job_run_id,
        "seed_senate_votes",
        "Seeding Senate votes from Senate.gov...",
        progress_total=500,
        congress=119,
        session=1,
        limit=500,
    )


@shared_task(bind=True, time_limit=1800, soft_time_limit=1700)
def run_seed_committees(self, job_run_id: int):
    """Seed committees and member assignments."""
    _run_management_command(
        job_run_id,
        "seed_committees",
        "Seeding committees from Congress.gov...",
        congress=119,
    )


@shared_task(bind=True, time_limit=600, soft_time_limit=550)
def run_seed_members(self, job_run_id: int):
    """Seed all current members from Congress.gov."""
    _run_management_command(
        job_run_id,
        "seed_members",
        "Seeding members from Congress.gov...",
    )


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_backfill_member_votes(self, job_run_id: int):
    """Backfill member vote records for votes missing them."""
    _run_management_command(
        job_run_id,
        "backfill_member_votes",
        "Backfilling member votes...",
    )


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_link_votes_to_bills(self, job_run_id: int):
    """Link votes to their related bills."""
    _run_management_command(
        job_run_id,
        "link_votes_to_bills",
        "Linking votes to bills...",
    )


@shared_task(bind=True, time_limit=7200, soft_time_limit=7000)
def run_generate_weekly_summaries(self, job_run_id: int):
    """Generate weekly recap and preview summaries for all weeks with activity."""
    from datetime import date, timedelta

    from apps.congress.models import Bill, Vote
    from apps.content.models import WeeklySummary
    from prompts import WEEKLY_PREVIEW_VERSION, WEEKLY_RECAP_VERSION
    from services import AIService, CacheService

    try:
        # Find the range of congressional activity
        earliest_vote = (
            Vote.objects.order_by("date").values_list("date", flat=True).first()
        )
        earliest_bill = (
            Bill.objects.exclude(latest_action_date__isnull=True)
            .order_by("latest_action_date")
            .values_list("latest_action_date", flat=True)
            .first()
        )

        if not earliest_vote and not earliest_bill:
            _start_job(job_run_id, 0)
            _complete_job(job_run_id, 0, 0, {"message": "No votes or bills found"})
            return

        earliest = min(filter(None, [earliest_vote, earliest_bill]))
        today = date.today()

        # Build list of (year, week_number, week_start, week_end) for every
        # ISO week from the earliest activity to now.
        weeks = []
        # Start from the Monday of the earliest week
        iso = earliest.isocalendar()
        current = earliest - timedelta(days=iso[2] - 1)  # Monday of that week
        while current <= today:
            year, wk, _ = current.isocalendar()
            week_start = current
            week_end = current + timedelta(days=6)
            weeks.append((year, wk, week_start, week_end))
            current += timedelta(days=7)

        # Pre-load existing summaries for fast lookup
        existing_recaps = set(
            WeeklySummary.objects.filter(
                summary_type="recap", prompt_version=WEEKLY_RECAP_VERSION
            ).values_list("year", "week_number")
        )
        existing_previews = set(
            WeeklySummary.objects.filter(
                summary_type="preview", prompt_version=WEEKLY_PREVIEW_VERSION
            ).values_list("year", "week_number")
        )

        # Build work items: (year, week, type, week_start, week_end)
        work_items = []
        for year, wk, week_start, week_end in weeks:
            if (year, wk) not in existing_recaps:
                work_items.append((year, wk, "recap", week_start, week_end))
            if (year, wk) not in existing_previews:
                work_items.append((year, wk, "preview", week_start, week_end))

        _start_job(job_run_id, len(work_items))

        if not work_items:
            _complete_job(
                job_run_id, 0, 0, {"message": "All weekly summaries already exist"}
            )
            return

        ai_service = AIService()
        succeeded = 0
        failed = 0
        errors = []

        for i, (year, wk, summary_type, week_start, week_end) in enumerate(
            work_items, 1
        ):
            label = f"{year}-W{wk:02d} {summary_type}"
            _update_progress(
                job_run_id,
                i - 1,
                f"[{i}/{len(work_items)}] Generating: {label}",
            )

            try:
                if summary_type == "recap":
                    # Gather votes for this week
                    votes = (
                        Vote.objects.filter(date__gte=week_start, date__lte=week_end)
                        .select_related("bill")
                        .order_by("-date", "-time")[:20]
                    )
                    vote_lines = []
                    for v in votes:
                        line = (
                            f"- {v.date}: {v.description} - {v.result.upper()} "
                            f"(Yea: {v.total_yea}, Nay: {v.total_nay})"
                            f"{' [Bipartisan]' if v.is_bipartisan else ''}"
                        )
                        if v.ai_summary:
                            line += f"\n  Summary: {v.ai_summary}"
                        vote_lines.append(line)
                    votes_text = (
                        "\n".join(vote_lines)
                        if vote_lines
                        else "No votes recorded this week."
                    )
                    vote_ids = [v.vote_id for v in votes]

                    # Gather bills with action this week
                    bills = Bill.objects.filter(
                        latest_action_date__gte=week_start,
                        latest_action_date__lte=week_end,
                    ).order_by("-latest_action_date")[:15]
                    bill_lines = []
                    for b in bills:
                        line = (
                            f"- {b.display_number}: "
                            f"{b.short_title or b.title[:100]} - "
                            f"{b.latest_action_text}"
                        )
                        if b.ai_summary:
                            line += f"\n  Summary: {b.ai_summary}"
                        bill_lines.append(line)
                    bills_text = (
                        "\n".join(bill_lines)
                        if bill_lines
                        else "No significant bill activity this week."
                    )
                    bill_ids = [b.bill_id for b in bills]

                    content, tokens = ai_service.generate_weekly_recap(
                        week_start=str(week_start),
                        week_end=str(week_end),
                        votes_summary=votes_text,
                        bills_summary=bills_text,
                    )

                    WeeklySummary.objects.update_or_create(
                        year=year,
                        week_number=wk,
                        summary_type="recap",
                        defaults={
                            "content": content,
                            "model_used": ai_service.MODEL,
                            "prompt_version": WEEKLY_RECAP_VERSION,
                            "tokens_used": tokens,
                            "votes_included": vote_ids,
                            "bills_included": bill_ids,
                        },
                    )
                    CacheService.invalidate_weekly_summary(year, wk, "recap")

                else:
                    # Preview: gather recently active bills leading into that week
                    lookback = week_start - timedelta(days=14)
                    pending_bills = Bill.objects.filter(
                        latest_action_date__gte=lookback,
                        latest_action_date__lt=week_start,
                    ).order_by("-latest_action_date")[:10]
                    pending_lines = []
                    for b in pending_bills:
                        line = (
                            f"- {b.display_number}: "
                            f"{b.short_title or b.title[:100]}"
                        )
                        if b.ai_summary:
                            line += f"\n  Summary: {b.ai_summary}"
                        pending_lines.append(line)
                    pending_text = (
                        "\n".join(pending_lines)
                        if pending_lines
                        else "No bills currently pending action."
                    )
                    bill_ids = [b.bill_id for b in pending_bills]

                    week_friday = week_start + timedelta(days=4)
                    content, tokens = ai_service.generate_weekly_preview(
                        week_start=str(week_start),
                        week_end=str(week_friday),
                        scheduled_votes="Check congress.gov for the latest floor schedule.",
                        pending_bills=pending_text,
                        hearings="Check committee websites for hearing schedules.",
                    )

                    WeeklySummary.objects.update_or_create(
                        year=year,
                        week_number=wk,
                        summary_type="preview",
                        defaults={
                            "content": content,
                            "model_used": ai_service.MODEL,
                            "prompt_version": WEEKLY_PREVIEW_VERSION,
                            "tokens_used": tokens,
                            "votes_included": [],
                            "bills_included": bill_ids,
                        },
                    )
                    CacheService.invalidate_weekly_summary(year, wk, "preview")

                succeeded += 1

            except Exception as e:
                failed += 1
                errors.append({"week": label, "error": str(e)})
                logger.error(f"Job {job_run_id}: error on {label}: {e}")

            _update_progress(job_run_id, i, f"Done: {label}")

        _complete_job(job_run_id, succeeded, failed, {"errors": errors[:50]})

    except Exception as e:
        logger.error(f"Job {job_run_id} crashed: {e}\n{traceback.format_exc()}")
        _fail_job(job_run_id, str(e))
