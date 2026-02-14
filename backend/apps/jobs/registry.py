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
}
