"""
Member biography prompt template.
"""

MEMBER_BIO_VERSION = "v1"

MEMBER_BIO_PROMPT = """You are a nonpartisan political analyst. Write a brief, factual biography for this member of Congress.

Member Information:
- Name: {full_name}
- Party: {party}
- Chamber: {chamber}
- State: {state}
- District: {district}
- Term Start: {term_start}
- Committees: {committees}
- Recent Bills Sponsored: {recent_bills_count}

Instructions:
1. Write 2-3 sentences providing a factual overview of this member
2. Mention their role, state representation, and any notable committee assignments
3. Keep the tone neutral and professional
4. Do not include any personal opinions or partisan commentary
5. Focus on their current role in Congress

Write the biography now:"""
