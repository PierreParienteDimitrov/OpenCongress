"""
Link existing votes to bills.

House votes: batch-fetch legislation info from Congress.gov list endpoint.
Senate votes: fetch bill info from Senate.gov XML detail files.

Usage:
    python manage.py link_votes_to_bills
    python manage.py link_votes_to_bills --dry-run
    python manage.py link_votes_to_bills --limit=50
"""

import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Bill, Vote

TYPE_DISPLAY = {
    "hr": "H.R.",
    "s": "S.",
    "hjres": "H.J.Res.",
    "sjres": "S.J.Res.",
    "hconres": "H.Con.Res.",
    "sconres": "S.Con.Res.",
    "hres": "H.Res.",
    "sres": "S.Res.",
}

# Senate XML document_type → bill_type
SENATE_DOC_TYPE_MAP = {
    "S.": "s",
    "H.R.": "hr",
    "S.J.Res.": "sjres",
    "H.J.Res.": "hjres",
    "S.Con.Res.": "sconres",
    "H.Con.Res.": "hconres",
    "S.Res.": "sres",
    "H.Res.": "hres",
}

# Regex fallback for parsing Senate <issue> field
BILL_PATTERNS = [
    (r"S\.\s*(\d+)", "s"),
    (r"H\.R\.\s*(\d+)", "hr"),
    (r"S\.J\.Res\.\s*(\d+)", "sjres"),
    (r"H\.J\.Res\.\s*(\d+)", "hjres"),
    (r"S\.Con\.Res\.\s*(\d+)", "sconres"),
    (r"H\.Con\.Res\.\s*(\d+)", "hconres"),
    (r"S\.Res\.\s*(\d+)", "sres"),
    (r"H\.Res\.\s*(\d+)", "hres"),
]


class Command(BaseCommand):
    help = "Link existing votes to bills using Congress.gov API and Senate.gov XML"

    CONGRESS_API_BASE = "https://api.congress.gov/v3"
    SENATE_VOTE_URL = (
        "https://www.senate.gov/legislative/LIS/roll_call_votes/"
        "vote{congress}{session}/vote_{congress}_{session}_{roll_call:05d}.xml"
    )

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.api_key = ""
        self.bills_created = 0

    def add_arguments(self, parser):
        parser.add_argument(
            "--congress",
            type=int,
            default=119,
            help="Congress number (default: 119)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of votes to process (0 = all)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't save changes, just show what would be linked",
        )

    def handle(self, *args, **options):
        self.api_key = os.environ.get("CONGRESS_API_KEY", "")
        if not self.api_key:
            self.stderr.write(
                self.style.ERROR("CONGRESS_API_KEY not set in environment")
            )
            return

        congress = options["congress"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        # Partition unlinked votes by chamber
        unlinked = Vote.objects.filter(bill__isnull=True)
        house_votes = list(
            unlinked.filter(chamber="house", congress=congress).values_list(
                "vote_id", "congress", "session", "roll_call", "question"
            )
        )
        senate_votes = list(
            unlinked.filter(chamber="senate", congress=congress).values_list(
                "vote_id", "congress", "session", "roll_call", "question"
            )
        )

        total = len(house_votes) + len(senate_votes)
        self.stdout.write(
            f"Found {total} unlinked votes "
            f"({len(house_votes)} house, {len(senate_votes)} senate)"
        )

        if limit > 0:
            house_votes = house_votes[:limit]
            remaining = max(0, limit - len(house_votes))
            senate_votes = senate_votes[:remaining]

        # Phase 1: House votes (batch from Congress.gov list endpoint)
        h_linked, h_no_leg, h_not_found = self._link_house_votes(
            house_votes, congress, dry_run
        )

        # Phase 2: Senate votes (individual XML from Senate.gov)
        s_linked, s_no_leg, s_not_found = self._link_senate_votes(
            senate_votes, congress, dry_run
        )

        linked = h_linked + s_linked
        no_leg = h_no_leg + s_no_leg
        not_found = h_not_found + s_not_found

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Linked: {linked}, Bills created: {self.bills_created}, "
                f"No legislation: {no_leg}, Bills not found: {not_found}"
            )
        )

    # ------------------------------------------------------------------
    # Phase 1: House votes — batch from Congress.gov list endpoint
    # ------------------------------------------------------------------

    def _fetch_house_legislation_map(
        self, congress: int
    ) -> dict[tuple[int, int], tuple[str, int]]:
        """
        Paginate Congress.gov house-vote list to build a lookup map.
        Returns {(session, roll_call): (bill_type, number)} for votes with legislation.
        """
        leg_map: dict[tuple[int, int], tuple[str, int]] = {}
        offset = 0

        while True:
            url = f"{self.CONGRESS_API_BASE}/house-vote/{congress}"
            params = {
                "api_key": self.api_key,
                "limit": 50,
                "offset": offset,
                "format": "json",
            }

            data = self._api_get_with_retry(url, params)
            if data is None:
                break

            votes = data.get("houseRollCallVotes", [])
            if not votes:
                break

            for v in votes:
                session_raw = v.get("sessionNumber")
                roll_call_raw = v.get("rollCallNumber")
                leg_type = v.get("legislationType", "")
                leg_number = v.get("legislationNumber")

                if session_raw is None or roll_call_raw is None:
                    continue

                if leg_type and leg_number:
                    bill_type = leg_type.lower().replace(".", "").replace(" ", "")
                    leg_map[(int(session_raw), int(roll_call_raw))] = (
                        bill_type,
                        int(leg_number),
                    )

            self.stdout.write(
                f"  Fetched {offset + len(votes)} house votes from API..."
            )

            if not data.get("pagination", {}).get("next"):
                break

            offset += len(votes)
            time.sleep(0.3)

        return leg_map

    def _link_house_votes(
        self,
        house_votes: list[tuple],
        congress: int,
        dry_run: bool,
    ) -> tuple[int, int, int]:
        """Link house votes using batch-fetched legislation data."""
        if not house_votes:
            return 0, 0, 0

        self.stdout.write(f"Phase 1: Linking {len(house_votes)} house votes...")

        leg_map = self._fetch_house_legislation_map(congress)
        self.stdout.write(
            f"  Built legislation map: {len(leg_map)} votes have legislation"
        )

        linked = 0
        no_legislation = 0
        bill_not_found = 0

        for i, (vote_id, v_congress, session, roll_call, question) in enumerate(
            house_votes
        ):
            leg_info = leg_map.get((session, roll_call))

            if leg_info is None:
                no_legislation += 1
            else:
                bill_type, number = leg_info
                bill = self._find_or_create_bill(bill_type, number, v_congress, dry_run)
                if bill:
                    if not dry_run:
                        self._link_vote(vote_id, bill, question)
                    linked += 1
                else:
                    bill_not_found += 1

            processed = i + 1
            if processed % 50 == 0 or processed == len(house_votes):
                self.stdout.write(
                    f"  Processed {processed} house votes, linked {linked}..."
                )

        return linked, no_legislation, bill_not_found

    # ------------------------------------------------------------------
    # Phase 2: Senate votes — fetch XML from Senate.gov
    # ------------------------------------------------------------------

    def _link_senate_votes(
        self,
        senate_votes: list[tuple],
        congress: int,
        dry_run: bool,
    ) -> tuple[int, int, int]:
        """Link senate votes by fetching XML from Senate.gov."""
        if not senate_votes:
            return 0, 0, 0

        self.stdout.write(f"Phase 2: Linking {len(senate_votes)} senate votes...")

        linked = 0
        no_legislation = 0
        bill_not_found = 0

        for i, (vote_id, v_congress, session, roll_call, question) in enumerate(
            senate_votes
        ):
            bill_type, number = self._fetch_senate_vote_bill_info(
                v_congress, session, roll_call
            )

            if bill_type is None or number is None:
                no_legislation += 1
            else:
                bill_id = f"{bill_type}{number}-{v_congress}"
                try:
                    bill = Bill.objects.get(bill_id=bill_id)
                    if not dry_run:
                        self._link_vote(vote_id, bill, question)
                    linked += 1
                except Bill.DoesNotExist:
                    bill_not_found += 1

            processed = i + 1
            if processed % 50 == 0 or processed == len(senate_votes):
                self.stdout.write(
                    f"  Processed {processed} senate votes, linked {linked}..."
                )

            time.sleep(0.3)

        return linked, no_legislation, bill_not_found

    def _fetch_senate_vote_bill_info(
        self, congress: int, session: int, roll_call: int
    ) -> tuple[str | None, int | None]:
        """
        Fetch Senate vote XML and extract bill info.
        Tries <document> element first, falls back to regex on <issue>.
        """
        url = self.SENATE_VOTE_URL.format(
            congress=congress, session=session, roll_call=roll_call
        )

        content = None
        for attempt in range(3):
            try:
                if attempt > 0:
                    time.sleep(2.0 * attempt)
                response = requests.get(url, timeout=(10, 30))
                response.raise_for_status()
                content = response.content
                break
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(
                        f"  Failed to fetch senate XML "
                        f"senate-{congress}-{session}-{roll_call}: {e}"
                    )

        if content is None:
            return None, None

        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return None, None

        # Approach 1: structured <document> element
        doc_elem = root.find("document")
        if doc_elem is not None:
            doc_type = self._xml_text(doc_elem, "document_type")
            doc_number = self._xml_text(doc_elem, "document_number")
            if doc_type and doc_number:
                bill_type = SENATE_DOC_TYPE_MAP.get(doc_type.strip())
                if bill_type:
                    try:
                        return bill_type, int(doc_number)
                    except ValueError:
                        pass

        # Approach 2: regex on <issue> text (fallback)
        issue = self._xml_text(root, "issue")
        if issue:
            for pattern, bill_type in BILL_PATTERNS:
                match = re.search(pattern, issue, re.IGNORECASE)
                if match:
                    try:
                        return bill_type, int(match.group(1))
                    except ValueError:
                        pass

        return None, None

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _api_get_with_retry(
        self, url: str, params: dict, max_attempts: int = 3
    ) -> dict | None:
        """GET request to Congress.gov with retry + backoff."""
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    time.sleep(2.0 * attempt)
                else:
                    time.sleep(0.3)
                response = requests.get(url, params=params, timeout=(10, 30))
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == max_attempts - 1:
                    self.stderr.write(
                        f"  API request failed after {max_attempts} attempts: {e}"
                    )
        return None

    def _find_or_create_bill(
        self, bill_type: str, number: int, congress: int, dry_run: bool
    ) -> Bill | None:
        """Find existing bill or create from Congress.gov API."""
        bill_id = f"{bill_type}{number}-{congress}"

        try:
            return Bill.objects.get(bill_id=bill_id)
        except Bill.DoesNotExist:
            pass

        if dry_run:
            self.stdout.write(f"    Would create bill: {bill_id}")
            self.bills_created += 1
            return Bill(bill_id=bill_id)

        bill = self._fetch_and_create_bill(bill_type, number, congress)
        if bill:
            self.bills_created += 1
        return bill

    def _fetch_and_create_bill(
        self, bill_type: str, number: int, congress: int
    ) -> Bill | None:
        """Fetch bill details from Congress.gov API and create Bill record."""
        url = f"{self.CONGRESS_API_BASE}/bill/{congress}/{bill_type}/{number}"
        params = {"api_key": self.api_key, "format": "json"}

        data = self._api_get_with_retry(url, params)
        if data is None:
            return None

        bill_data = data.get("bill", {})
        if not bill_data:
            return None

        bill_id = f"{bill_type}{number}-{congress}"

        # Parse dates
        introduced_date = None
        intro_str = bill_data.get("introducedDate")
        if intro_str:
            try:
                introduced_date = datetime.strptime(intro_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        latest_action_date = None
        latest_action_text = ""
        latest_action = bill_data.get("latestAction", {})
        if latest_action:
            action_date_str = latest_action.get("actionDate")
            if action_date_str:
                try:
                    latest_action_date = datetime.strptime(
                        action_date_str, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass
            latest_action_text = latest_action.get("text", "")

        display_number = f"{TYPE_DISPLAY.get(bill_type, bill_type.upper())} {number}"

        bill = Bill.objects.create(
            bill_id=bill_id,
            bill_type=bill_type,
            number=number,
            congress=congress,
            title=bill_data.get("title", ""),
            short_title=bill_data.get("shortTitle") or "",
            display_number=display_number,
            introduced_date=introduced_date,
            latest_action_date=latest_action_date,
            latest_action_text=latest_action_text,
            congress_url=bill_data.get("url", ""),
        )

        self.stdout.write(f"    Created bill: {bill_id}")
        return bill

    def _link_vote(self, vote_id: str, bill: Bill, question: str) -> None:
        """Update a vote to link it to a bill and enrich description."""
        update: dict[str, Any] = {"bill": bill}
        bill_title = bill.short_title or bill.title
        if bill_title and bill.display_number:
            update["description"] = f"{question} - {bill.display_number}: {bill_title}"
        Vote.objects.filter(vote_id=vote_id).update(**update)

    @staticmethod
    def _xml_text(elem: ET.Element, tag: str) -> str | None:
        """Safely extract text from an XML child element."""
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
