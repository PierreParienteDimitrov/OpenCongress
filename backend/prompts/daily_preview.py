"""
Daily preview prompt template.
"""

DAILY_PREVIEW_VERSION = "v1"

DAILY_PREVIEW_PROMPT = """You are a nonpartisan congressional correspondent. Write a brief preview of tomorrow's expected congressional activity.

Date: {date}

Recently Active Bills (may see action):
{pending_bills}

Recent Votes (context for ongoing activity):
{recent_votes}

Instructions:
1. Write 1-2 short paragraphs previewing what to watch for tomorrow
2. Mention bills that may see floor action based on recent momentum
3. Note any patterns in recent activity that suggest what's next
4. Keep the tone informative and nonpartisan
5. Write for a general audience, avoiding jargon
6. Be factual — do not speculate about outcomes
7. If there is little expected activity, keep it brief

Write the daily preview now:"""
