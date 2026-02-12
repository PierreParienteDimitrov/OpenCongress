"""
AI content generation tasks.
"""

import logging
from datetime import date, timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_bill_summary(self, bill_id: str) -> dict:
    """
    Generate an AI summary for a single bill.

    Args:
        bill_id: The bill ID to generate a summary for

    Returns:
        Dict with success status and summary info
    """
    from apps.congress.models import Bill
    from prompts import BILL_SUMMARY_VERSION
    from services import AIService, CacheService

    try:
        bill = Bill.objects.select_related("sponsor").get(bill_id=bill_id)
    except Bill.DoesNotExist:
        logger.error(f"Bill not found: {bill_id}")
        return {"success": False, "error": "Bill not found"}

    try:
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
        bill.ai_summary_model = AIService.MODEL
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
            "model": AIService.MODEL,
        }

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
    ).values_list("bill_id", flat=True)[:50]  # Process up to 50 per run

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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_member_bio(self, bioguide_id: str) -> dict:
    """
    Generate an AI biography for a single member.

    Args:
        bioguide_id: The member's bioguide ID

    Returns:
        Dict with success status and bio info
    """
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

    try:
        ai_service = AIService()

        # Get committee names
        committees = [ca.committee.name for ca in member.committee_assignments.all()]

        # Count recent bills
        recent_bills_count = member.sponsored_bills.count()

        bio, tokens = ai_service.generate_member_bio(
            full_name=member.full_name,
            party=member.party,
            chamber=member.chamber,
            state=member.state,
            district=member.district,
            term_start=str(member.term_start) if member.term_start else None,
            committees=committees,
            recent_bills_count=recent_bills_count,
        )

        # Update the member
        member.ai_bio = bio
        member.ai_bio_model = AIService.MODEL
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
        CacheService.invalidate_member(bioguide_id, member.chamber)

        logger.info(f"Generated bio for member {bioguide_id} ({tokens} tokens)")

        return {
            "success": True,
            "bioguide_id": bioguide_id,
            "tokens": tokens,
            "model": AIService.MODEL,
        }

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

        votes_summary = (
            "\n".join(
                [
                    f"- {v.date}: {v.description} - {v.result.upper()} "
                    f"(Yea: {v.total_yea}, Nay: {v.total_nay})"
                    f"{' [Bipartisan]' if v.is_bipartisan else ''}"
                    for v in votes
                ]
            )
            if votes
            else "No votes recorded this week."
        )

        vote_ids = [v.vote_id for v in votes]

        # Get bills with action this week
        bills = Bill.objects.filter(
            latest_action_date__gte=week_start, latest_action_date__lte=week_end
        ).order_by("-latest_action_date")[:15]

        bills_summary = (
            "\n".join(
                [
                    f"- {b.display_number}: {b.short_title or b.title[:100]} - {b.latest_action_text}"
                    for b in bills
                ]
            )
            if bills
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
            model_used=AIService.MODEL,
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

        pending_bills_summary = (
            "\n".join(
                [
                    f"- {b.display_number}: {b.short_title or b.title[:100]}"
                    for b in pending_bills
                ]
            )
            if pending_bills
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
            model_used=AIService.MODEL,
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
