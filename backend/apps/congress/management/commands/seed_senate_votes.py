"""
Seed Senate votes from Senate.gov XML.

Congress.gov API doesn't support Senate votes yet, so we fetch directly from Senate.gov.

Usage:
    python manage.py seed_senate_votes --congress=119 --session=1 --limit=100
"""

import re
import time as time_module
import xml.etree.ElementTree as ET
from datetime import date, datetime, time
from typing import Any

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.congress.models import Bill, Member, MemberVote, Vote

# US state name to abbreviation mapping
STATE_ABBREVS = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
    "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
    "florida": "fl", "georgia": "ga", "hawaii": "hi", "idaho": "id",
    "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
    "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn", "mississippi": "ms",
    "missouri": "mo", "montana": "mt", "nebraska": "ne", "nevada": "nv",
    "new hampshire": "nh", "new jersey": "nj", "new mexico": "nm", "new york": "ny",
    "north carolina": "nc", "north dakota": "nd", "ohio": "oh", "oklahoma": "ok",
    "oregon": "or", "pennsylvania": "pa", "rhode island": "ri", "south carolina": "sc",
    "south dakota": "sd", "tennessee": "tn", "texas": "tx", "utah": "ut",
    "vermont": "vt", "virginia": "va", "washington": "wa", "west virginia": "wv",
    "wisconsin": "wi", "wyoming": "wy", "district of columbia": "dc",
    "puerto rico": "pr", "guam": "gu", "virgin islands": "vi",
    "american samoa": "as", "northern mariana islands": "mp",
}


class Command(BaseCommand):
    help = "Seed Senate votes from Senate.gov XML"

    VOTE_LIST_URL = "https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{congress}_{session}.xml"
    VOTE_DETAIL_URL = "https://www.senate.gov/legislative/LIS/roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{roll_call:05d}.xml"

    def add_arguments(self, parser):
        parser.add_argument(
            "--congress",
            type=int,
            default=119,
            help="Congress number (default: 119)",
        )
        parser.add_argument(
            "--session",
            type=int,
            default=1,
            help="Session number (default: 1)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Number of votes to fetch (default: 100)",
        )

    def handle(self, *args, **options):
        congress = options["congress"]
        session = options["session"]
        limit = options["limit"]

        self.stdout.write(f"Fetching Senate votes for Congress {congress}, Session {session}...")

        # Build member lookup cache (last_name + state -> member)
        self.member_cache = self._build_member_cache()
        self.stdout.write(f"  Cached {len(self.member_cache)} senators for matching")

        votes_created, member_votes_created = self._fetch_votes(congress, session, limit)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {votes_created} votes with {member_votes_created} member votes"
            )
        )

    def _build_member_cache(self) -> dict:
        """Build a cache for matching senators by last_name + state abbreviation."""
        cache = {}
        senators = Member.objects.filter(chamber="senate")
        for member in senators:
            # Get last_name - either from field or parse from full_name
            last_name = member.last_name
            first_name = member.first_name

            # If last_name is empty, parse from full_name (format: "Last, First")
            if not last_name and member.full_name:
                parts = member.full_name.split(",")
                if parts:
                    last_name = parts[0].strip()
                    if len(parts) > 1:
                        # First name may include middle initial, take first word
                        first_parts = parts[1].strip().split()
                        first_name = first_parts[0] if first_parts else ""

            if not last_name:
                continue

            # Normalize state to abbreviation
            state = member.state.lower()
            state_abbrev = STATE_ABBREVS.get(state, state)

            # Primary key: last_name + state abbreviation
            key = f"{last_name.lower()}_{state_abbrev}"
            cache[key] = member

            # Also store by full name for fallback
            if first_name:
                full_key = f"{first_name.lower()}_{last_name.lower()}_{state_abbrev}"
                cache[full_key] = member

        return cache

    def _fetch_votes(self, congress: int, session: int, limit: int) -> tuple[int, int]:
        """Fetch vote list from Senate.gov and process each vote."""
        url = self.VOTE_LIST_URL.format(congress=congress, session=session)

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch vote list: {e}"))
            return 0, 0

        # Parse XML
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            self.stderr.write(self.style.ERROR(f"Failed to parse vote list XML: {e}"))
            return 0, 0

        # Get all votes from the XML
        votes_elem = root.find("votes")
        if votes_elem is None:
            self.stdout.write("  No votes found in XML")
            return 0, 0

        vote_elements = votes_elem.findall("vote")
        self.stdout.write(f"  Found {len(vote_elements)} votes in list")

        votes_created = 0
        member_votes_created = 0

        for vote_elem in vote_elements:
            if votes_created >= limit:
                break

            v_created, mv_created = self._process_vote(vote_elem, congress, session)
            votes_created += v_created
            member_votes_created += mv_created

            if votes_created % 10 == 0 and votes_created > 0:
                self.stdout.write(f"  Processed {votes_created} votes so far...")

        return votes_created, member_votes_created

    def _process_vote(self, vote_elem: ET.Element, congress: int, session: int) -> tuple[int, int]:
        """Process a single vote from the list and fetch its details."""
        # Get roll call number from vote_number element
        vote_number_text = self._get_text(vote_elem, "vote_number")
        if not vote_number_text:
            return 0, 0

        try:
            roll_call = int(vote_number_text)
        except ValueError:
            return 0, 0

        vote_id = f"senate-{congress}-{session}-{roll_call}"

        # Check if vote already exists
        if Vote.objects.filter(vote_id=vote_id).exists():
            return 0, 0

        # Fetch detailed vote XML
        detail_url = self.VOTE_DETAIL_URL.format(
            congress=congress,
            session=session,
            roll_call=roll_call,
        )

        try:
            time_module.sleep(0.3)  # Rate limiting
            response = requests.get(detail_url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            self.stderr.write(f"  Failed to fetch vote {vote_id}: {e}")
            return 0, 0

        try:
            detail_root = ET.fromstring(response.content)
        except ET.ParseError as e:
            self.stderr.write(f"  Failed to parse vote {vote_id} XML: {e}")
            return 0, 0

        # Parse vote details
        vote_date = self._parse_date(self._get_text(detail_root, "vote_date"))
        if vote_date is None:
            self.stderr.write(f"  Skipping vote {vote_id}: no date found")
            return 0, 0
        vote_time = self._parse_time(self._get_text(detail_root, "vote_date"))
        question = self._get_text(detail_root, "question") or ""
        question_text = self._get_text(detail_root, "vote_question_text") or question
        vote_title = self._get_text(detail_root, "vote_title") or ""
        vote_result = self._get_text(detail_root, "vote_result") or ""

        # Parse totals from count element
        count_elem = detail_root.find("count")
        total_yea = self._get_int(count_elem, "yeas")
        total_nay = self._get_int(count_elem, "nays")
        total_present = self._get_int(count_elem, "present")
        total_not_voting = self._get_int(count_elem, "absent")

        # Parse individual member votes and calculate party totals
        members_elem = detail_root.find("members")
        member_votes_data, party_totals = self._parse_member_votes(members_elem)

        # Map result to our choices
        result = self._map_result(vote_result)

        # Try to link to a bill from issue field
        bill = self._find_bill(self._get_text(vote_elem, "issue"), congress)

        # Determine if bipartisan (both parties majority voting same way)
        dem_majority_yea = party_totals["D"]["yea"] > party_totals["D"]["nay"]
        rep_majority_yea = party_totals["R"]["yea"] > party_totals["R"]["nay"]
        is_bipartisan = dem_majority_yea == rep_majority_yea

        # Build description from title and question
        description = vote_title if vote_title else question_text

        # Build source URL
        source_url = detail_url

        # Create vote in a transaction
        with transaction.atomic():
            vote = Vote.objects.create(
                vote_id=vote_id,
                chamber="senate",
                congress=congress,
                session=session,
                roll_call=roll_call,
                date=vote_date,
                time=vote_time,
                question=question[:200] if question else "",
                question_text=question_text,
                description=description,
                vote_type="",
                result=result,
                bill=bill,
                total_yea=total_yea,
                total_nay=total_nay,
                total_present=total_present,
                total_not_voting=total_not_voting,
                dem_yea=party_totals["D"]["yea"],
                dem_nay=party_totals["D"]["nay"],
                dem_present=party_totals["D"]["present"],
                dem_not_voting=party_totals["D"]["not_voting"],
                rep_yea=party_totals["R"]["yea"],
                rep_nay=party_totals["R"]["nay"],
                rep_present=party_totals["R"]["present"],
                rep_not_voting=party_totals["R"]["not_voting"],
                ind_yea=party_totals["I"]["yea"],
                ind_nay=party_totals["I"]["nay"],
                ind_present=party_totals["I"]["present"],
                ind_not_voting=party_totals["I"]["not_voting"],
                is_bipartisan=is_bipartisan,
                source_url=source_url,
            )

            # Create member votes
            member_votes_created = self._create_member_votes(vote, member_votes_data)

        return 1, member_votes_created

    def _parse_member_votes(self, members_elem: ET.Element | None) -> tuple[list[dict], dict]:
        """Parse member votes and calculate party totals."""
        party_totals = {
            "D": {"yea": 0, "nay": 0, "present": 0, "not_voting": 0},
            "R": {"yea": 0, "nay": 0, "present": 0, "not_voting": 0},
            "I": {"yea": 0, "nay": 0, "present": 0, "not_voting": 0},
        }
        member_votes_data: list[dict[str, Any]] = []

        if members_elem is None:
            return member_votes_data, party_totals

        for member_elem in members_elem.findall("member"):
            last_name = self._get_text(member_elem, "last_name") or ""
            first_name = self._get_text(member_elem, "first_name") or ""
            party = self._get_text(member_elem, "party") or ""
            state = self._get_text(member_elem, "state") or ""
            vote_cast = self._get_text(member_elem, "vote_cast") or ""

            # Map vote cast to position
            position = self._map_vote_cast(vote_cast)

            # Store member vote data for later creation
            member_votes_data.append({
                "last_name": last_name,
                "first_name": first_name,
                "party": party,
                "state": state,
                "position": position,
            })

            # Update party totals
            party_key = party if party in party_totals else "I"
            if position == "yea":
                party_totals[party_key]["yea"] += 1
            elif position == "nay":
                party_totals[party_key]["nay"] += 1
            elif position == "present":
                party_totals[party_key]["present"] += 1
            else:
                party_totals[party_key]["not_voting"] += 1

        return member_votes_data, party_totals

    def _create_member_votes(self, vote: Vote, member_votes_data: list[dict]) -> int:
        """Create MemberVote records for each senator's vote."""
        created = 0

        for mv_data in member_votes_data:
            member = self._find_member(
                mv_data["last_name"],
                mv_data["first_name"],
                mv_data["state"],
            )

            if member is None:
                continue

            try:
                MemberVote.objects.create(
                    vote=vote,
                    member=member,
                    position=mv_data["position"],
                )
                created += 1
            except Exception:
                pass

        return created

    def _find_member(self, last_name: str, first_name: str, state: str) -> Member | None:
        """Find a member in the cache by name and state."""
        # Try primary lookup: last_name + state
        key = f"{last_name.lower()}_{state.lower()}"
        if key in self.member_cache:
            return self.member_cache[key]

        # Try full name lookup
        full_key = f"{first_name.lower()}_{last_name.lower()}_{state.lower()}"
        if full_key in self.member_cache:
            return self.member_cache[full_key]

        return None

    def _find_bill(self, issue: str | None, congress: int) -> Bill | None:
        """Try to find a bill from the issue field (e.g., 'S. 123')."""
        if not issue:
            return None

        # Match patterns like "S. 123", "H.R. 456", "S.J.Res. 7"
        patterns = [
            (r"S\.\s*(\d+)", "s"),
            (r"H\.R\.\s*(\d+)", "hr"),
            (r"S\.J\.Res\.\s*(\d+)", "sjres"),
            (r"H\.J\.Res\.\s*(\d+)", "hjres"),
            (r"S\.Con\.Res\.\s*(\d+)", "sconres"),
            (r"H\.Con\.Res\.\s*(\d+)", "hconres"),
            (r"S\.Res\.\s*(\d+)", "sres"),
            (r"H\.Res\.\s*(\d+)", "hres"),
        ]

        for pattern, bill_type in patterns:
            match = re.search(pattern, issue, re.IGNORECASE)
            if match:
                number = match.group(1)
                bill_id = f"{bill_type}{number}-{congress}"
                try:
                    return Bill.objects.get(bill_id=bill_id)
                except Bill.DoesNotExist:
                    pass

        return None

    def _map_vote_cast(self, vote_cast: str) -> str:
        """Map Senate XML vote_cast to our Position choices."""
        vote_lower = vote_cast.lower().strip()
        if vote_lower in ("yea", "aye"):
            return "yea"
        elif vote_lower in ("nay", "no"):
            return "nay"
        elif vote_lower == "present":
            return "present"
        else:
            return "not_voting"

    def _map_result(self, result: str) -> str:
        """Map Senate result string to Vote.VoteResult choices."""
        result_lower = result.lower()
        if "confirmed" in result_lower or "agreed" in result_lower:
            return "agreed"
        elif "rejected" in result_lower or "not confirmed" in result_lower:
            return "rejected"
        elif "passed" in result_lower:
            return "passed"
        elif "failed" in result_lower or "not sustained" in result_lower:
            return "failed"
        return "agreed"  # Default for Senate procedural votes

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date from Senate XML format (e.g., 'January 9, 2025, 02:54 PM')."""
        if not date_str:
            return None

        # Try various formats
        formats = [
            "%B %d, %Y, %I:%M %p",  # "January 9, 2025, 02:54 PM"
            "%B %d, %Y",            # "January 9, 2025"
            "%Y-%m-%d",             # "2025-01-09"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        return None

    def _parse_time(self, date_str: str | None) -> time | None:
        """Parse time from Senate XML format."""
        if not date_str:
            return None

        try:
            # Format: "January 9, 2025, 02:54 PM"
            dt = datetime.strptime(date_str.strip(), "%B %d, %Y, %I:%M %p")
            return dt.time()
        except ValueError:
            return None

    def _get_text(self, elem: ET.Element | None, tag: str) -> str | None:
        """Safely get text from an XML element."""
        if elem is None:
            return None
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None

    def _get_int(self, elem: ET.Element | None, tag: str) -> int:
        """Safely get integer from an XML element."""
        text = self._get_text(elem, tag)
        if text:
            try:
                return int(text)
            except ValueError:
                pass
        return 0
