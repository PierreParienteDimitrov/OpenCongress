"""
AI Service - Wrapper for Google Gen AI SDK (Gemini).
"""

import logging

from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class AIService:
    """Service for generating AI content using Gemini."""

    MODEL = "gemini-2.5-flash"

    def __init__(self):
        api_key = getattr(settings, "GOOGLE_API_KEY", None)
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not configured in settings")
        self.client = genai.Client(api_key=api_key)

    def generate_completion(
        self, prompt: str, max_tokens: int = 200
    ) -> tuple[str, int]:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of output tokens

        Returns:
            Tuple of (generated text, total tokens used)
        """
        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=0,
                    ),
                ),
            )

            text = response.text.strip()
            tokens = response.usage_metadata.total_token_count

            logger.info(f"Generated completion with {tokens} tokens using {self.MODEL}")

            return text, tokens

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

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
        committees: list[str],
        recent_bills_count: int,
    ) -> tuple[str, int]:
        """Generate a biographical summary for a member."""
        from prompts import MEMBER_BIO_PROMPT

        party_name = {"D": "Democrat", "R": "Republican", "I": "Independent"}.get(
            party, party
        )
        chamber_name = "House of Representatives" if chamber == "house" else "Senate"
        district_str = f"District {district}" if district else "At-large"

        prompt = MEMBER_BIO_PROMPT.format(
            full_name=full_name,
            party=party_name,
            chamber=chamber_name,
            state=state,
            district=district_str if chamber == "house" else "N/A",
            term_start=term_start or "Unknown",
            committees=", ".join(committees) if committees else "None listed",
            recent_bills_count=recent_bills_count,
        )

        return self.generate_completion(prompt, max_tokens=200)

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
