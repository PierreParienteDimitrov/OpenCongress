"""
Job type registry.

Each entry defines:
  - label: Human-readable name for the admin UI
  - task: Dotted path to the Celery wrapper task
  - queue: Which Celery queue to dispatch to
  - description: Shown in the admin dashboard
"""

JOB_REGISTRY = {
    "generate_member_bios": {
        "label": "Generate All Missing Member Bios",
        "task": "apps.jobs.tasks.run_generate_member_bios",
        "queue": "ai",
        "description": (
            "Generate AI bios for all active members missing one "
            "or with outdated prompt version."
        ),
    },
    "generate_bill_summaries": {
        "label": "Generate All Missing Bill Summaries",
        "task": "apps.jobs.tasks.run_generate_bill_summaries",
        "queue": "ai",
        "description": (
            "Generate AI summaries for all bills missing one "
            "or with outdated prompt version."
        ),
    },
    "generate_vote_summaries": {
        "label": "Generate All Missing Vote Summaries",
        "task": "apps.jobs.tasks.run_generate_vote_summaries",
        "queue": "ai",
        "description": (
            "Generate AI summaries for all votes missing one "
            "or with outdated prompt version."
        ),
    },
    "generate_weekly_summaries": {
        "label": "Generate All Missing Weekly Summaries",
        "task": "apps.jobs.tasks.run_generate_weekly_summaries",
        "queue": "ai",
        "description": (
            "Generate weekly recap and preview summaries for all weeks "
            "with congressional activity that are missing or outdated."
        ),
    },
    "sync_members": {
        "label": "Sync Members from Congress.gov",
        "task": "apps.jobs.tasks.run_sync_members",
        "queue": "sync",
        "description": (
            "Fetch and update all current members from the Congress.gov API."
        ),
    },
    "sync_recent_votes": {
        "label": "Sync Recent Votes",
        "task": "apps.jobs.tasks.run_sync_recent_votes",
        "queue": "sync",
        "description": (
            "Sync recent votes from House (Congress.gov) and Senate (Senate.gov)."
        ),
    },
    # --- Seed commands (data import from Congress.gov) ---
    "seed_bills": {
        "label": "Seed Bills from Congress.gov",
        "task": "apps.jobs.tasks.run_seed_bills",
        "queue": "sync",
        "description": (
            "Import HR and S bills for Congress 119 from Congress.gov API "
            "(fetches up to 5000 bills)."
        ),
    },
    "seed_votes": {
        "label": "Seed Votes from Congress.gov",
        "task": "apps.jobs.tasks.run_seed_votes",
        "queue": "sync",
        "description": (
            "Import House and Senate votes for Congress 119 from Congress.gov API "
            "(fetches up to 2000 votes)."
        ),
    },
    "seed_senate_votes": {
        "label": "Seed Senate Votes from Senate.gov",
        "task": "apps.jobs.tasks.run_seed_senate_votes",
        "queue": "sync",
        "description": (
            "Import Senate votes for Congress 119 Session 1 from Senate.gov XML."
        ),
    },
    "seed_committees": {
        "label": "Seed Committees from Congress.gov",
        "task": "apps.jobs.tasks.run_seed_committees",
        "queue": "sync",
        "description": ("Import committees and member assignments for Congress 119."),
    },
    "seed_members": {
        "label": "Seed Members from Congress.gov",
        "task": "apps.jobs.tasks.run_seed_members",
        "queue": "sync",
        "description": (
            "Import all current members from Congress.gov API + social media data."
        ),
    },
    "backfill_member_votes": {
        "label": "Backfill Member Votes",
        "task": "apps.jobs.tasks.run_backfill_member_votes",
        "queue": "sync",
        "description": (
            "Backfill individual member vote records for votes that are missing them."
        ),
    },
    "link_votes_to_bills": {
        "label": "Link Votes to Bills",
        "task": "apps.jobs.tasks.run_link_votes_to_bills",
        "queue": "sync",
        "description": (
            "Link Vote records to their related Bill records. "
            "House: batch from Congress.gov list API. Senate: from Senate.gov XML."
        ),
    },
    "generate_daily_summaries": {
        "label": "Generate All Missing Daily Summaries",
        "task": "apps.jobs.tasks.run_generate_daily_summaries",
        "queue": "ai",
        "description": (
            "Generate daily recap and preview summaries for all weekdays "
            "from Jan 2026 to today that are missing or outdated."
        ),
    },
    "generate_committee_summaries": {
        "label": "Generate Committee Summaries",
        "task": "tasks.ai.generate_committee_summaries",
        "queue": "ai",
        "description": (
            "Generate AI summaries for committees that need them (up to 50 per run)."
        ),
    },
}
