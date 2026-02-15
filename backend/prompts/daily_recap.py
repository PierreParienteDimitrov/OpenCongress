"""
Daily recap prompt template.
"""

DAILY_RECAP_VERSION = "v1"

DAILY_RECAP_PROMPT = """You are a nonpartisan congressional correspondent. Write a brief summary of today's congressional activity.

Date: {date}

Votes Today:
{votes_summary}

Bills with Action Today:
{bills_summary}

Instructions:
1. Write 1-3 short paragraphs summarizing the day's key congressional activity
2. Highlight any significant votes and their outcomes
3. Mention bills that advanced or saw action
4. Note bipartisan vs party-line dynamics where relevant
5. Keep the tone informative and nonpartisan
6. Write for a general audience, avoiding jargon
7. If there was little activity, keep it brief — one short paragraph is fine

Write the daily recap now:"""
