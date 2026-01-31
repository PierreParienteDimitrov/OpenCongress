"""
Weekly recap prompt template.
"""

WEEKLY_RECAP_VERSION = "v1"

WEEKLY_RECAP_PROMPT = """You are a nonpartisan congressional correspondent. Write a summary of this week's congressional activity for citizens who want to stay informed.

Week: {week_start} to {week_end}

Votes This Week:
{votes_summary}

Bills with Action:
{bills_summary}

Instructions:
1. Write 3-5 paragraphs summarizing the week's key congressional activity
2. Highlight the most significant votes and their outcomes
3. Mention any notable bills that advanced or were introduced
4. Note any bipartisan votes or significant party-line votes
5. Keep the tone informative and nonpartisan
6. Write for a general audience, avoiding jargon
7. Focus on what actually happened, not speculation

Write the weekly recap now:"""
