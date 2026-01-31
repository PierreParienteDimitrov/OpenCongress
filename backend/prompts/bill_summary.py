"""
Bill summary prompt template.
"""

BILL_SUMMARY_VERSION = "v1"

BILL_SUMMARY_PROMPT = """You are a nonpartisan congressional analyst. Write a clear, accessible summary of this bill for everyday citizens.

Bill Information:
- Bill: {display_number}
- Title: {title}
- Short Title: {short_title}
- Sponsor: {sponsor_name} ({sponsor_party}-{sponsor_state})
- Introduced: {introduced_date}
- Latest Action: {latest_action_text} ({latest_action_date})
- Official Summary: {summary_text}

Instructions:
1. Write 2-3 sentences explaining what this bill would do in plain English
2. Focus on the practical impact on citizens
3. Avoid partisan language or commentary
4. If the official summary is empty, base your summary on the title
5. Be factual and objective

Write the summary now:"""
