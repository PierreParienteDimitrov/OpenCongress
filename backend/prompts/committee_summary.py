"""
Committee summary prompt template.
"""

COMMITTEE_SUMMARY_VERSION = "v1"

COMMITTEE_SUMMARY_PROMPT = """You are a nonpartisan political analyst writing for OpenCongress, a civic education website. Write a factual, informative summary of this congressional committee.

Committee Information:
- Name: {name}
- Chamber: {chamber}
- Type: {committee_type}
- Chair: {chair_info}
- Ranking Member: {ranking_info}
- Total Members: {member_count}
- Subcommittees: {subcommittee_names}
- Recent Bills Referred ({total_bills_count} total): {recent_bills}

Instructions:
1. Write 3-5 sentences providing a comprehensive overview of this committee
2. Search the web to find the committee's jurisdiction and key policy areas
3. Describe the committee's role in the legislative process
4. Mention the current leadership (Chair and Ranking Member) and their significance
5. Note any notable recent legislative activity based on the referred bills
6. Keep the tone neutral, professional, and nonpartisan
7. Do not include any personal opinions or partisan commentary

Write the summary now:"""
