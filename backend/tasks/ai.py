"""
AI content generation tasks.
"""

import logging
from datetime import date, timedelta

from celery import shared_task
from celery.exceptions import Retry as CeleryRetry
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


def _generate_bill_summary_core(bill_id: str) -> dict:
    """
    Core logic for generating an AI summary for a single bill.

    Called directly by the job runner (no Celery retry overhead) and
    wrapped by the Celery task for async/scheduled use.
    """
    from apps.congress.models import Bill
    from prompts import BILL_SUMMARY_VERSION
    from services import AIService, CacheService

    try:
        bill = Bill.objects.select_related("sponsor").get(bill_id=bill_id)
    except Bill.DoesNotExist:
        logger.error(f"Bill not found: {bill_id}")
        return {"success": False, "error": "Bill not found"}

    ai_service = AIService()

    sponsor_name = bill.sponsor.full_name if bill.sponsor else None
    sponsor_party = bill.sponsor.party if bill.sponsor else None
    sponsor_state = bill.sponsor.state if bill.sponsor else None

    summary, tokens = ai_service.generate_bill_summary(
        display_number=bill.display_number,
        title=bill.title,
        short_title=bill.short_title,
        sponsor_name=sponsor_name,
        sponsor_party=sponsor_party,
        sponsor_state=sponsor_state,
        introduced_date=str(bill.introduced_date) if bill.introduced_date else None,
        latest_action_text=bill.latest_action_text,
        latest_action_date=(
            str(bill.latest_action_date) if bill.latest_action_date else None
        ),
        summary_text=bill.summary_text,
    )

    # Update the bill
    bill.ai_summary = summary
    bill.ai_summary_model = ai_service.MODEL
    bill.ai_summary_created_at = timezone.now()
    bill.ai_summary_prompt_version = BILL_SUMMARY_VERSION
    bill.save(
        update_fields=[
            "ai_summary",
            "ai_summary_model",
            "ai_summary_created_at",
            "ai_summary_prompt_version",
        ]
    )

    # Invalidate caches
    CacheService.invalidate_bill(bill_id)

    logger.info(f"Generated summary for bill {bill_id} ({tokens} tokens)")

    return {
        "success": True,
        "bill_id": bill_id,
        "tokens": tokens,
        "model": ai_service.MODEL,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_bill_summary(self, bill_id: str) -> dict:
    """Celery task wrapper — adds retry behaviour for async/scheduled use."""
    try:
        return _generate_bill_summary_core(bill_id)
    except Exception as e:
        logger.error(f"Error generating summary for bill {bill_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def generate_bill_summaries() -> dict:
    """
    Batch generate summaries for bills that need them.
    Runs daily at 6:30am.

    Returns:
        Dict with processing statistics
    """
    from apps.congress.models import Bill

    # Find bills without summaries or with outdated prompt versions
    from prompts import BILL_SUMMARY_VERSION

    bills_needing_summaries = Bill.objects.filter(
        Q(ai_summary="") | ~Q(ai_summary_prompt_version=BILL_SUMMARY_VERSION)
    ).values_list("bill_id", flat=True)[
        :50
    ]  # Process up to 50 per run

    processed = 0
    errors = 0

    for bill_id in bills_needing_summaries:
        try:
            generate_bill_summary.delay(bill_id)
            processed += 1
        except Exception as e:
            logger.error(f"Failed to queue summary for bill {bill_id}: {e}")
            errors += 1

    logger.info(f"Queued {processed} bill summaries, {errors} errors")

    return {
        "queued": processed,
        "errors": errors,
        "total_needing_summaries": len(bills_needing_summaries),
    }


def _generate_member_bio_core(bioguide_id: str) -> dict:
    """Core logic for generating an AI biography for a single member."""
    from apps.congress.models import Member
    from prompts import MEMBER_BIO_VERSION
    from services import AIService, CacheService

    try:
        member = Member.objects.prefetch_related(
            "committee_assignments__committee"
        ).get(bioguide_id=bioguide_id)
    except Member.DoesNotExist:
        logger.error(f"Member not found: {bioguide_id}")
        return {"success": False, "error": "Member not found"}

    ai_service = AIService()

    # Get committee names WITH roles (Chair, Ranking Member, Member)
    committee_roles = [
        (ca.committee.name, ca.get_role_display())
        for ca in member.committee_assignments.all()
    ]

    # Get top 5 sponsored bill titles (most recently active)
    top_bills = list(
        member.sponsored_bills.exclude(short_title="")
        .order_by("-latest_action_date")
        .values_list("short_title", flat=True)[:5]
    )
    # Fallback: if no short_titles, use truncated full titles
    if not top_bills:
        top_bills = [
            title[:80]
            for title in member.sponsored_bills.order_by(
                "-latest_action_date"
            ).values_list("title", flat=True)[:5]
        ]

    # Total bills count
    total_bills_count = member.sponsored_bills.count()

    bio, tokens = ai_service.generate_member_bio(
        full_name=member.full_name,
        party=member.party,
        chamber=member.chamber,
        state=member.state,
        district=member.district,
        term_start=(str(member.term_start) if member.term_start else None),
        seniority_date=(str(member.seniority_date) if member.seniority_date else None),
        birth_date=(str(member.birth_date) if member.birth_date else None),
        gender=member.gender,
        committee_roles=committee_roles,
        top_bills=top_bills,
        total_bills_count=total_bills_count,
    )

    # Update the member
    member.ai_bio = bio
    member.ai_bio_model = ai_service.MODEL
    member.ai_bio_created_at = timezone.now()
    member.ai_bio_prompt_version = MEMBER_BIO_VERSION
    member.save(
        update_fields=[
            "ai_bio",
            "ai_bio_model",
            "ai_bio_created_at",
            "ai_bio_prompt_version",
        ]
    )

    # Invalidate caches
    CacheService.invalidate_member(bioguide_id, member.chamber, member.full_name)

    logger.info(f"Generated bio for member {bioguide_id} ({tokens} tokens)")

    return {
        "success": True,
        "bioguide_id": bioguide_id,
        "tokens": tokens,
        "model": ai_service.MODEL,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_member_bio(self, bioguide_id: str) -> dict:
    """Celery task wrapper — adds retry behaviour for async/scheduled use."""
    try:
        return _generate_member_bio_core(bioguide_id)
    except Exception as e:
        logger.error(f"Error generating bio for member {bioguide_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def generate_member_bios() -> dict:
    """
    Batch generate bios for members that need them.
    Runs Monday at 5am.

    Returns:
        Dict with processing statistics
    """
    from apps.congress.models import Member

    from prompts import MEMBER_BIO_VERSION

    # Find active members without bios or with outdated prompt versions
    members_needing_bios = (
        Member.objects.filter(is_active=True)
        .filter(Q(ai_bio="") | ~Q(ai_bio_prompt_version=MEMBER_BIO_VERSION))
        .values_list("bioguide_id", flat=True)[:50]
    )  # Process up to 50 per run

    processed = 0
    errors = 0

    for bioguide_id in members_needing_bios:
        try:
            generate_member_bio.delay(bioguide_id)
            processed += 1
        except Exception as e:
            logger.error(f"Failed to queue bio for member {bioguide_id}: {e}")
            errors += 1

    logger.info(f"Queued {processed} member bios, {errors} errors")

    return {
        "queued": processed,
        "errors": errors,
        "total_needing_bios": len(members_needing_bios),
    }


def _generate_vote_summary_core(vote_id: str) -> dict:
    """Core logic for generating an AI summary for a single vote."""
    from apps.congress.models import Vote
    from prompts import VOTE_SUMMARY_VERSION
    from services import AIService, CacheService

    try:
        vote = Vote.objects.select_related("bill").get(vote_id=vote_id)
    except Vote.DoesNotExist:
        logger.error(f"Vote not found: {vote_id}")
        return {"success": False, "error": "Vote not found"}

    ai_service = AIService()

    bill_display_number = vote.bill.display_number if vote.bill else None
    bill_title = vote.bill.short_title or vote.bill.title if vote.bill else None

    summary, tokens = ai_service.generate_vote_summary(
        chamber=vote.chamber,
        date=str(vote.date),
        question=vote.question,
        vote_type=vote.vote_type,
        result=vote.result,
        bill_display_number=bill_display_number,
        bill_title=bill_title,
        total_yea=vote.total_yea,
        total_nay=vote.total_nay,
        dem_yea=vote.dem_yea,
        dem_nay=vote.dem_nay,
        rep_yea=vote.rep_yea,
        rep_nay=vote.rep_nay,
        is_bipartisan=vote.is_bipartisan,
    )

    # Update the vote
    vote.ai_summary = summary
    vote.ai_summary_model = ai_service.MODEL
    vote.ai_summary_created_at = timezone.now()
    vote.ai_summary_prompt_version = VOTE_SUMMARY_VERSION
    vote.save(
        update_fields=[
            "ai_summary",
            "ai_summary_model",
            "ai_summary_created_at",
            "ai_summary_prompt_version",
        ]
    )

    # Invalidate caches
    CacheService.invalidate_vote(vote_id)

    logger.info(f"Generated summary for vote {vote_id} ({tokens} tokens)")

    return {
        "success": True,
        "vote_id": vote_id,
        "tokens": tokens,
        "model": ai_service.MODEL,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_vote_summary(self, vote_id: str) -> dict:
    """Celery task wrapper — adds retry behaviour for async/scheduled use."""
    try:
        return _generate_vote_summary_core(vote_id)
    except Exception as e:
        logger.error(f"Error generating summary for vote {vote_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def generate_vote_summaries() -> dict:
    """
    Batch generate summaries for votes that need them.
    Runs daily at 7am.

    Returns:
        Dict with processing statistics
    """
    from apps.congress.models import Vote

    from prompts import VOTE_SUMMARY_VERSION

    votes_needing_summaries = Vote.objects.filter(
        Q(ai_summary="") | ~Q(ai_summary_prompt_version=VOTE_SUMMARY_VERSION)
    ).values_list("vote_id", flat=True)[
        :50
    ]  # Process up to 50 per run

    processed = 0
    errors = 0

    for vote_id in votes_needing_summaries:
        try:
            generate_vote_summary.delay(vote_id)
            processed += 1
        except Exception as e:
            logger.error(f"Failed to queue summary for vote {vote_id}: {e}")
            errors += 1

    logger.info(f"Queued {processed} vote summaries, {errors} errors")

    return {
        "queued": processed,
        "errors": errors,
        "total_needing_summaries": len(votes_needing_summaries),
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_weekly_recap(self) -> dict:
    """
    Generate the weekly recap summary.
    Runs Saturday at 6am.

    Returns:
        Dict with success status and summary info
    """
    from apps.congress.models import Bill, Vote
    from apps.content.models import WeeklySummary
    from prompts import WEEKLY_RECAP_VERSION
    from services import AIService, CacheService

    # Calculate the week dates (Monday to Sunday of the week ending today)
    today = date.today()
    week_end = today
    week_start = today - timedelta(days=6)

    # Get ISO week number
    year, week_number, _ = today.isocalendar()

    # Check if we already have a recap for this week
    if WeeklySummary.objects.filter(
        year=year, week_number=week_number, summary_type="recap"
    ).exists():
        logger.info(f"Weekly recap already exists for {year}-W{week_number}")
        return {"success": True, "skipped": True, "reason": "Already exists"}

    try:
        ai_service = AIService()

        # Get votes from this week
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
        votes_summary = (
            "\n".join(vote_lines) if vote_lines else "No votes recorded this week."
        )

        vote_ids = [v.vote_id for v in votes]

        # Get bills with action this week
        bills = Bill.objects.filter(
            latest_action_date__gte=week_start, latest_action_date__lte=week_end
        ).order_by("-latest_action_date")[:15]

        bill_lines = []
        for b in bills:
            line = f"- {b.display_number}: {b.short_title or b.title[:100]} - {b.latest_action_text}"
            if b.ai_summary:
                line += f"\n  Summary: {b.ai_summary}"
            bill_lines.append(line)
        bills_summary = (
            "\n".join(bill_lines)
            if bill_lines
            else "No significant bill activity this week."
        )

        bill_ids = [b.bill_id for b in bills]

        # Generate the recap
        content, tokens = ai_service.generate_weekly_recap(
            week_start=str(week_start),
            week_end=str(week_end),
            votes_summary=votes_summary,
            bills_summary=bills_summary,
        )

        # Save the summary
        WeeklySummary.objects.create(
            year=year,
            week_number=week_number,
            summary_type="recap",
            content=content,
            model_used=ai_service.MODEL,
            prompt_version=WEEKLY_RECAP_VERSION,
            tokens_used=tokens,
            votes_included=vote_ids,
            bills_included=bill_ids,
        )

        # Invalidate caches
        CacheService.invalidate_weekly_summary(year, week_number, "recap")

        logger.info(
            f"Generated weekly recap for {year}-W{week_number} ({tokens} tokens)"
        )

        return {
            "success": True,
            "year": year,
            "week": week_number,
            "tokens": tokens,
            "votes_count": len(vote_ids),
            "bills_count": len(bill_ids),
        }

    except Exception as e:
        logger.error(f"Error generating weekly recap: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_weekly_preview(self) -> dict:
    """
    Generate the weekly preview summary.
    Runs Sunday at 6pm.

    Returns:
        Dict with success status and summary info
    """
    from apps.congress.models import Bill
    from apps.content.models import WeeklySummary
    from prompts import WEEKLY_PREVIEW_VERSION
    from services import AIService, CacheService

    # Calculate the upcoming week dates (Monday to Friday of next week)
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    week_start = today + timedelta(days=days_until_monday)
    week_end = week_start + timedelta(days=4)  # Friday

    # Get ISO week number for the upcoming week
    year, week_number, _ = week_start.isocalendar()

    # Check if we already have a preview for this week
    if WeeklySummary.objects.filter(
        year=year, week_number=week_number, summary_type="preview"
    ).exists():
        logger.info(f"Weekly preview already exists for {year}-W{week_number}")
        return {"success": True, "skipped": True, "reason": "Already exists"}

    try:
        ai_service = AIService()

        # Get recently active bills that may see action
        pending_bills = Bill.objects.filter(
            latest_action_date__gte=today - timedelta(days=14)
        ).order_by("-latest_action_date")[:10]

        pending_lines = []
        for b in pending_bills:
            line = f"- {b.display_number}: {b.short_title or b.title[:100]}"
            if b.ai_summary:
                line += f"\n  Summary: {b.ai_summary}"
            pending_lines.append(line)
        pending_bills_summary = (
            "\n".join(pending_lines)
            if pending_lines
            else "No bills currently pending action."
        )

        bill_ids = [b.bill_id for b in pending_bills]

        # Generate the preview
        # Note: We don't have real scheduled vote data, so we use a placeholder
        content, tokens = ai_service.generate_weekly_preview(
            week_start=str(week_start),
            week_end=str(week_end),
            scheduled_votes="Check congress.gov for the latest floor schedule.",
            pending_bills=pending_bills_summary,
            hearings="Check committee websites for hearing schedules.",
        )

        # Save the summary
        WeeklySummary.objects.create(
            year=year,
            week_number=week_number,
            summary_type="preview",
            content=content,
            model_used=ai_service.MODEL,
            prompt_version=WEEKLY_PREVIEW_VERSION,
            tokens_used=tokens,
            votes_included=[],
            bills_included=bill_ids,
        )

        # Invalidate caches
        CacheService.invalidate_weekly_summary(year, week_number, "preview")

        logger.info(
            f"Generated weekly preview for {year}-W{week_number} ({tokens} tokens)"
        )

        return {
            "success": True,
            "year": year,
            "week": week_number,
            "tokens": tokens,
            "bills_count": len(bill_ids),
        }

    except Exception as e:
        logger.error(f"Error generating weekly preview: {e}")
        raise self.retry(exc=e)


# ── Daily summary tasks ──────────────────────────────────────────────


def _generate_daily_recap_core(target_date: date) -> dict:
    """Core logic for generating a daily recap summary for a given date."""
    from apps.congress.models import Bill, Vote
    from apps.content.models import DailySummary
    from prompts import DAILY_RECAP_VERSION
    from services import AIService, CacheService

    # Check if we already have a recap for this date
    if DailySummary.objects.filter(date=target_date, summary_type="recap").exists():
        logger.info(f"Daily recap already exists for {target_date}")
        return {"success": True, "skipped": True, "reason": "Already exists"}

    ai_service = AIService()

    # Get votes for this date
    votes = (
        Vote.objects.filter(date=target_date)
        .select_related("bill")
        .order_by("-time")[:20]
    )

    vote_lines = []
    for v in votes:
        line = (
            f"- {v.description} - {v.result.upper()} "
            f"(Yea: {v.total_yea}, Nay: {v.total_nay})"
            f"{' [Bipartisan]' if v.is_bipartisan else ''}"
        )
        if v.ai_summary:
            line += f"\n  Summary: {v.ai_summary}"
        vote_lines.append(line)
    votes_summary = "\n".join(vote_lines) if vote_lines else "No votes recorded today."
    vote_ids = [v.vote_id for v in votes]

    # Get bills with action on this date
    bills = Bill.objects.filter(latest_action_date=target_date).order_by(
        "-latest_action_date"
    )[:15]

    bill_lines = []
    for b in bills:
        line = f"- {b.display_number}: {b.short_title or b.title[:100]} - {b.latest_action_text}"
        if b.ai_summary:
            line += f"\n  Summary: {b.ai_summary}"
        bill_lines.append(line)
    bills_summary = (
        "\n".join(bill_lines) if bill_lines else "No significant bill activity today."
    )
    bill_ids = [b.bill_id for b in bills]

    # Generate the recap
    content, tokens = ai_service.generate_daily_recap(
        date=str(target_date),
        votes_summary=votes_summary,
        bills_summary=bills_summary,
    )

    # Save the summary
    DailySummary.objects.create(
        date=target_date,
        summary_type="recap",
        content=content,
        model_used=ai_service.MODEL,
        prompt_version=DAILY_RECAP_VERSION,
        tokens_used=tokens,
        votes_included=vote_ids,
        bills_included=bill_ids,
    )

    # Invalidate caches
    CacheService.invalidate_daily_summary(target_date)

    logger.info(f"Generated daily recap for {target_date} ({tokens} tokens)")

    return {
        "success": True,
        "date": str(target_date),
        "tokens": tokens,
        "votes_count": len(vote_ids),
        "bills_count": len(bill_ids),
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_daily_recap(self, target_date_str: str = None) -> dict:
    """
    Generate a daily recap summary.
    Runs Mon-Fri at 10 PM ET.

    Args:
        target_date_str: ISO date string (YYYY-MM-DD). Defaults to today.
    """
    try:
        target = (
            date.fromisoformat(target_date_str) if target_date_str else date.today()
        )
        return _generate_daily_recap_core(target)
    except CeleryRetry:
        raise
    except Exception as e:
        logger.error(f"Error generating daily recap: {e}")
        raise self.retry(exc=e)


def _generate_daily_preview_core(target_date: date) -> dict:
    """Core logic for generating a daily preview summary for a given date."""
    from apps.congress.models import Bill, Vote
    from apps.content.models import DailySummary
    from prompts import DAILY_PREVIEW_VERSION
    from services import AIService, CacheService

    # Check if we already have a preview for this date
    if DailySummary.objects.filter(date=target_date, summary_type="preview").exists():
        logger.info(f"Daily preview already exists for {target_date}")
        return {"success": True, "skipped": True, "reason": "Already exists"}

    ai_service = AIService()

    # Get recently active bills (past 3 days) that may see action
    pending_bills = Bill.objects.filter(
        latest_action_date__gte=target_date - timedelta(days=3)
    ).order_by("-latest_action_date")[:10]

    pending_lines = []
    for b in pending_bills:
        line = f"- {b.display_number}: {b.short_title or b.title[:100]}"
        if b.ai_summary:
            line += f"\n  Summary: {b.ai_summary}"
        pending_lines.append(line)
    pending_bills_summary = (
        "\n".join(pending_lines)
        if pending_lines
        else "No bills currently pending action."
    )
    bill_ids = [b.bill_id for b in pending_bills]

    # Get recent votes (past 2 days) for context
    recent_votes = (
        Vote.objects.filter(date__gte=target_date - timedelta(days=2))
        .select_related("bill")
        .order_by("-date", "-time")[:10]
    )

    vote_lines = []
    for v in recent_votes:
        line = (
            f"- {v.date}: {v.description} - {v.result.upper()} "
            f"(Yea: {v.total_yea}, Nay: {v.total_nay})"
        )
        vote_lines.append(line)
    recent_votes_summary = "\n".join(vote_lines) if vote_lines else "No recent votes."

    # Generate the preview
    content, tokens = ai_service.generate_daily_preview(
        date=str(target_date),
        pending_bills=pending_bills_summary,
        recent_votes=recent_votes_summary,
    )

    # Save the summary
    DailySummary.objects.create(
        date=target_date,
        summary_type="preview",
        content=content,
        model_used=ai_service.MODEL,
        prompt_version=DAILY_PREVIEW_VERSION,
        tokens_used=tokens,
        votes_included=[],
        bills_included=bill_ids,
    )

    # Invalidate caches
    CacheService.invalidate_daily_summary(target_date)

    logger.info(f"Generated daily preview for {target_date} ({tokens} tokens)")

    return {
        "success": True,
        "date": str(target_date),
        "tokens": tokens,
        "bills_count": len(bill_ids),
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_daily_preview(self, target_date_str: str = None) -> dict:
    """
    Generate a daily preview summary.
    Runs Sun-Thu at 9 PM ET (preview for next weekday).

    Args:
        target_date_str: ISO date string (YYYY-MM-DD) for the day to preview.
            Defaults to the next weekday.
    """
    try:
        if target_date_str:
            target = date.fromisoformat(target_date_str)
        else:
            # Compute next weekday
            today = date.today()
            tomorrow = today + timedelta(days=1)
            # If tomorrow is Saturday, skip to Monday
            if tomorrow.weekday() == 5:  # Saturday
                tomorrow += timedelta(days=2)
            elif tomorrow.weekday() == 6:  # Sunday
                tomorrow += timedelta(days=1)
            target = tomorrow
        return _generate_daily_preview_core(target)
    except CeleryRetry:
        raise
    except Exception as e:
        logger.error(f"Error generating daily preview: {e}")
        raise self.retry(exc=e)


# ── Committee summary tasks ──────────────────────────────────────────


def _generate_committee_summary_core(committee_id: str) -> dict:
    """Core logic for generating an AI summary for a single committee."""
    from apps.congress.models import Committee
    from prompts import COMMITTEE_SUMMARY_VERSION
    from services import AIService, CacheService

    try:
        committee = Committee.objects.prefetch_related(
            "members__member",
            "subcommittees",
            "referred_bills__bill",
        ).get(committee_id=committee_id)
    except Committee.DoesNotExist:
        logger.error(f"Committee not found: {committee_id}")
        return {"success": False, "error": "Committee not found"}

    ai_service = AIService()

    # Get chair info
    chair_info = "Vacant"
    try:
        chair_cm = committee.members.select_related("member").get(role="chair")
        m = chair_cm.member
        chair_info = f"{m.full_name} ({m.party}-{m.state})"
    except Exception:
        pass

    # Get ranking member info
    ranking_info = "Vacant"
    try:
        ranking_cm = committee.members.select_related("member").get(role="ranking")
        m = ranking_cm.member
        ranking_info = f"{m.full_name} ({m.party}-{m.state})"
    except Exception:
        pass

    # Get member count
    member_count = committee.members.count()

    # Get subcommittee names
    subs = list(committee.subcommittees.values_list("name", flat=True))
    subcommittee_names = ", ".join(subs) if subs else "None"

    # Get recent referred bills
    recent_bill_committees = committee.referred_bills.select_related("bill").order_by(
        "-bill__latest_action_date"
    )[:10]
    bill_lines = [
        f"{bc.bill.display_number}: {bc.bill.short_title or bc.bill.title[:80]}"
        for bc in recent_bill_committees
    ]
    recent_bills = "; ".join(bill_lines) if bill_lines else "None"
    total_bills_count = committee.referred_bills.count()

    summary, tokens = ai_service.generate_committee_summary(
        name=committee.name,
        chamber=committee.chamber,
        committee_type=committee.get_committee_type_display(),
        chair_info=chair_info,
        ranking_info=ranking_info,
        member_count=member_count,
        subcommittee_names=subcommittee_names,
        recent_bills=recent_bills,
        total_bills_count=total_bills_count,
    )

    # Update the committee
    committee.ai_summary = summary
    committee.ai_summary_model = ai_service.MODEL
    committee.ai_summary_created_at = timezone.now()
    committee.ai_summary_prompt_version = COMMITTEE_SUMMARY_VERSION
    committee.save(
        update_fields=[
            "ai_summary",
            "ai_summary_model",
            "ai_summary_created_at",
            "ai_summary_prompt_version",
        ]
    )

    # Invalidate caches
    CacheService.invalidate_committee(committee_id)

    logger.info(f"Generated summary for committee {committee_id} ({tokens} tokens)")

    return {
        "success": True,
        "committee_id": committee_id,
        "tokens": tokens,
        "model": ai_service.MODEL,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_committee_summary(self, committee_id: str) -> dict:
    """Celery task wrapper — adds retry behaviour for async/scheduled use."""
    try:
        return _generate_committee_summary_core(committee_id)
    except Exception as e:
        logger.error(f"Error generating summary for committee {committee_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def generate_committee_summaries() -> dict:
    """
    Batch generate summaries for committees that need them.

    Returns:
        Dict with processing statistics
    """
    from apps.congress.models import Committee

    from prompts import COMMITTEE_SUMMARY_VERSION

    # Only top-level committees (not subcommittees)
    committees_needing_summaries = (
        Committee.objects.filter(parent_committee__isnull=True)
        .filter(
            Q(ai_summary="") | ~Q(ai_summary_prompt_version=COMMITTEE_SUMMARY_VERSION)
        )
        .values_list("committee_id", flat=True)[:50]
    )

    processed = 0
    errors = 0

    for committee_id in committees_needing_summaries:
        try:
            generate_committee_summary.delay(committee_id)
            processed += 1
        except Exception as e:
            logger.error(f"Failed to queue summary for committee {committee_id}: {e}")
            errors += 1

    logger.info(f"Queued {processed} committee summaries, {errors} errors")

    return {
        "queued": processed,
        "errors": errors,
        "total_needing_summaries": len(committees_needing_summaries),
    }
