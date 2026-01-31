"""
AI Service - Wrapper for Google Generative AI (Gemini).
"""

import logging

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for generating AI content using Gemini."""

    MODEL = "gemini-2.5-flash"

    def __init__(self):
        api_key = getattr(settings, "GOOGLE_API_KEY", None)
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not configured in settings")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.MODEL)

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
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,
                ),
            )

            text = response.text.strip()
            tokens = response.usage_metadata.total_token_count

            logger.info(
                f"Generated completion with {tokens} tokens using {self.MODEL}"
            )

            return text, tokens

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

    def generate_bill_summary(
        self,
        display_number: str,
        title: str,
        short_title: str,
        sponsor_name: str,
        sponsor_party: str,
        sponsor_state: str,
        introduced_date: str,
        latest_action_text: str,
        latest_action_date: str,
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
        district: str | None,
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
