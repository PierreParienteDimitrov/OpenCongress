"""
AI Service - Multi-provider wrapper (Anthropic, Gemini, OpenAI).

The active provider is controlled by the ``AI_PROVIDER`` setting
(default ``"anthropic"``).  Each provider needs its own API-key setting:

    AI_PROVIDER=anthropic  →  ANTHROPIC_API_KEY
    AI_PROVIDER=gemini     →  GOOGLE_API_KEY
    AI_PROVIDER=openai     →  OPENAI_API_KEY
"""

import logging

from django.conf import settings

from .ai_providers import PROVIDERS

logger = logging.getLogger(__name__)

# Maps provider name → Django setting that holds the API key
_KEY_SETTINGS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class AIService:
    """High-level service for generating AI content.

    All domain methods (bill summaries, vote summaries, …) live here.
    The low-level LLM call is delegated to whichever provider is active.
    """

    def __init__(self):
        provider_name = getattr(settings, "AI_PROVIDER", "anthropic")
        if provider_name not in PROVIDERS:
            raise ValueError(
                f"Unknown AI_PROVIDER '{provider_name}'. "
                f"Choose from: {', '.join(PROVIDERS)}"
            )

        key_setting = _KEY_SETTINGS[provider_name]
        api_key = getattr(settings, key_setting, None)
        if not api_key:
            raise ValueError(f"{key_setting} is not configured in settings")

        self._provider = PROVIDERS[provider_name](api_key)

    @property
    def MODEL(self) -> str:  # noqa: N802 – kept uppercase for back-compat
        return self._provider.MODEL

    # ── Low-level completions ────────────────────────────────────────

    def generate_completion(
        self, prompt: str, max_tokens: int = 200
    ) -> tuple[str, int]:
        """Generate a plain completion.

        Returns:
            Tuple of (generated text, total tokens used)
        """
        try:
            text, tokens = self._provider.generate(prompt, max_tokens, temperature=0.3)
            logger.info(f"Generated completion with {tokens} tokens using {self.MODEL}")
            return text, tokens
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

    def generate_completion_with_web_search(
        self, prompt: str, max_tokens: int = 400
    ) -> tuple[str, int]:
        """Generate a completion with web-search grounding.

        Returns:
            Tuple of (generated text, total tokens used)
        """
        try:
            text, tokens = self._provider.generate_with_web_search(
                prompt, max_tokens, temperature=0.3
            )
            logger.info(
                f"Generated web-search completion with {tokens} tokens "
                f"using {self.MODEL}"
            )
            return text, tokens
        except Exception as e:
            logger.error(f"Error generating web-search completion: {e}")
            raise

    # ── Domain helpers (unchanged public API) ────────────────────────

    def generate_bill_summary(
        self,
        display_number: str,
        title: str,
        short_title: str,
        sponsor_name: str | None,
        sponsor_party: str | None,
        sponsor_state: str | None,
        introduced_date: str | None,
        latest_action_text: str,
        latest_action_date: str | None,
        summary_text: str,
    ) -> tuple[str, int]:
        """Generate a plain-English summary for a bill."""
        from prompts import BILL_SUMMARY_PROMPT

        prompt = BILL_SUMMARY_PROMPT.format(
            display_number=display_number,
            title=title,
            short_title=short_title or "N/A",
            sponsor_name=sponsor_name or "Unknown",
            sponsor_party=sponsor_party or "Unknown",
            sponsor_state=sponsor_state or "Unknown",
            introduced_date=introduced_date or "Unknown",
            latest_action_text=latest_action_text or "No action recorded",
            latest_action_date=latest_action_date or "Unknown",
            summary_text=summary_text or "No official summary available",
        )

        return self.generate_completion(prompt, max_tokens=200)

    def generate_member_bio(
        self,
        full_name: str,
        party: str,
        chamber: str,
        state: str,
        district: int | None,
        term_start: str | None,
        seniority_date: str | None,
        birth_date: str | None,
        gender: str,
        committee_roles: list[tuple[str, str]],
        top_bills: list[str],
        total_bills_count: int,
    ) -> tuple[str, int]:
        """Generate a biographical summary for a member using web search."""
        from prompts import MEMBER_BIO_PROMPT

        party_name = {"D": "Democrat", "R": "Republican", "I": "Independent"}.get(
            party, party
        )
        chamber_name = "House of Representatives" if chamber == "house" else "Senate"
        district_str = f"District {district}" if district else "At-large"

        # Map gender to pronouns
        gender_map = {
            "M": ("He", "him"),
            "F": ("She", "her"),
        }
        pronoun_subject, pronoun_object = gender_map.get(gender, ("They", "them"))

        # Format committee roles: "Committee Name (Role)"
        if committee_roles:
            formatted_committees = ", ".join(
                f"{name} ({role})" for name, role in committee_roles
            )
        else:
            formatted_committees = "None listed"

        # Format top bills
        formatted_bills = "; ".join(top_bills[:5]) if top_bills else "None"

        prompt = MEMBER_BIO_PROMPT.format(
            full_name=full_name,
            party=party_name,
            chamber=chamber_name,
            state=state,
            district=district_str if chamber == "house" else "N/A",
            gender={"M": "Male", "F": "Female"}.get(gender, "Unknown"),
            birth_date=birth_date or "Unknown",
            term_start=term_start or "Unknown",
            seniority_date=seniority_date or "Unknown",
            committee_roles=formatted_committees,
            top_bills=formatted_bills,
            total_bills_count=total_bills_count,
            pronoun_subject=pronoun_subject,
            pronoun_object=pronoun_object,
        )

        return self.generate_completion_with_web_search(prompt, max_tokens=400)

    def generate_vote_summary(
        self,
        chamber: str,
        date: str,
        question: str,
        vote_type: str,
        result: str,
        bill_display_number: str | None,
        bill_title: str | None,
        total_yea: int,
        total_nay: int,
        dem_yea: int,
        dem_nay: int,
        rep_yea: int,
        rep_nay: int,
        is_bipartisan: bool,
    ) -> tuple[str, int]:
        """Generate a plain-English summary for a vote."""
        from prompts import VOTE_SUMMARY_PROMPT

        chamber_name = "House of Representatives" if chamber == "house" else "Senate"

        prompt = VOTE_SUMMARY_PROMPT.format(
            chamber=chamber_name,
            date=date,
            question=question or "Unknown",
            vote_type=vote_type or "Unknown",
            result=result or "Unknown",
            bill_display_number=bill_display_number or "No linked bill",
            bill_title=bill_title or "N/A",
            total_yea=total_yea,
            total_nay=total_nay,
            dem_yea=dem_yea,
            dem_nay=dem_nay,
            rep_yea=rep_yea,
            rep_nay=rep_nay,
            is_bipartisan="Yes" if is_bipartisan else "No",
        )

        return self.generate_completion(prompt, max_tokens=200)

    def generate_weekly_recap(
        self,
        week_start: str,
        week_end: str,
        votes_summary: str,
        bills_summary: str,
    ) -> tuple[str, int]:
        """Generate a weekly recap summary."""
        from prompts import WEEKLY_RECAP_PROMPT

        prompt = WEEKLY_RECAP_PROMPT.format(
            week_start=week_start,
            week_end=week_end,
            votes_summary=votes_summary or "No votes recorded this week.",
            bills_summary=bills_summary or "No significant bill activity this week.",
        )

        return self.generate_completion(prompt, max_tokens=500)

    def generate_weekly_preview(
        self,
        week_start: str,
        week_end: str,
        scheduled_votes: str,
        pending_bills: str,
        hearings: str,
    ) -> tuple[str, int]:
        """Generate a weekly preview summary."""
        from prompts import WEEKLY_PREVIEW_PROMPT

        prompt = WEEKLY_PREVIEW_PROMPT.format(
            week_start=week_start,
            week_end=week_end,
            scheduled_votes=scheduled_votes or "No votes currently scheduled.",
            pending_bills=pending_bills or "No bills currently pending action.",
            hearings=hearings or "No hearings currently scheduled.",
        )

        return self.generate_completion(prompt, max_tokens=400)

    def generate_daily_recap(
        self,
        date: str,
        votes_summary: str,
        bills_summary: str,
    ) -> tuple[str, int]:
        """Generate a daily recap summary."""
        from prompts import DAILY_RECAP_PROMPT

        prompt = DAILY_RECAP_PROMPT.format(
            date=date,
            votes_summary=votes_summary or "No votes recorded today.",
            bills_summary=bills_summary or "No significant bill activity today.",
        )

        return self.generate_completion(prompt, max_tokens=300)

    def generate_daily_preview(
        self,
        date: str,
        pending_bills: str,
        recent_votes: str,
    ) -> tuple[str, int]:
        """Generate a daily preview summary."""
        from prompts import DAILY_PREVIEW_PROMPT

        prompt = DAILY_PREVIEW_PROMPT.format(
            date=date,
            pending_bills=pending_bills or "No bills currently pending action.",
            recent_votes=recent_votes or "No recent votes.",
        )

        return self.generate_completion(prompt, max_tokens=250)

    def generate_committee_summary(
        self,
        name: str,
        chamber: str,
        committee_type: str,
        chair_info: str,
        ranking_info: str,
        member_count: int,
        subcommittee_names: str,
        recent_bills: str,
        total_bills_count: int,
    ) -> tuple[str, int]:
        """Generate a summary for a committee using web search."""
        from prompts import COMMITTEE_SUMMARY_PROMPT

        chamber_name = "House of Representatives" if chamber == "house" else "Senate"

        prompt = COMMITTEE_SUMMARY_PROMPT.format(
            name=name,
            chamber=chamber_name,
            committee_type=committee_type or "Standing",
            chair_info=chair_info or "Vacant",
            ranking_info=ranking_info or "Vacant",
            member_count=member_count,
            subcommittee_names=subcommittee_names or "None",
            recent_bills=recent_bills or "None",
            total_bills_count=total_bills_count,
        )

        return self.generate_completion_with_web_search(prompt, max_tokens=300)
