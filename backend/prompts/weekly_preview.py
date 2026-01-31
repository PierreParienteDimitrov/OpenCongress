"""
Weekly preview prompt template.
"""

WEEKLY_PREVIEW_VERSION = "v1"

WEEKLY_PREVIEW_PROMPT = """You are a nonpartisan congressional correspondent. Write a preview of the upcoming week in Congress for citizens who want to stay informed.

Upcoming Week: {week_start} to {week_end}

Scheduled Votes:
{scheduled_votes}

Bills Expected for Action:
{pending_bills}

Committee Hearings:
{hearings}

Instructions:
1. Write 2-4 paragraphs previewing the week ahead in Congress
2. Highlight any significant votes or hearings scheduled
3. Mention key bills that may see action
4. Note any important deadlines or expected developments
5. Keep the tone informative and nonpartisan
6. Write for a general audience, avoiding jargon
7. Be factual about what is scheduled, avoid speculation about outcomes

Write the weekly preview now:"""
