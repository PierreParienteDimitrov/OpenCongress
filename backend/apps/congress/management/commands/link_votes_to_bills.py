"""
Link existing votes to bills by fetching data from Congress.gov API.
Creates bills if they don't exist.

Usage:
    python manage.py link_votes_to_bills
"""

import os
import time
from datetime import datetime
from typing import Any

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Bill, Vote


class Command(BaseCommand):
    help = "Link existing votes to bills using Congress.gov API"

    CONGRESS_API_BASE = "https://api.congress.gov/v3"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.api_key = ""
        self.bills_created = 0

    def add_arguments(self, parser):
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
            self.stderr.write(self.style.ERROR("CONGRESS_API_KEY not set in environment"))
            return

        limit = options["limit"]
        dry_run = options["dry_run"]

        # Get votes without bills
        votes_without_bills = Vote.objects.filter(bill__isnull=True)
        total_count = votes_without_bills.count()

        self.stdout.write(f"Found {total_count} votes without linked bills")

        if limit > 0:
            votes_without_bills = votes_without_bills[:limit]
            self.stdout.write(f"Processing first {limit} votes")

        linked_count = 0
        not_found_count = 0
        error_count = 0

        for i, vote in enumerate(votes_without_bills):
            if i > 0 and i % 50 == 0:
                self.stdout.write(
                    f"  Processed {i} votes, linked {linked_count}, created {self.bills_created} bills..."
                )

            result = self._try_link_vote(vote, dry_run)
            if result == "linked":
                linked_count += 1
            elif result == "not_found":
                not_found_count += 1
            else:
                error_count += 1

            # Rate limiting
            time.sleep(0.2)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Linked: {linked_count}, Bills created: {self.bills_created}, "
                f"No legislation: {not_found_count}, Errors: {error_count}"
            )
        )

    def _try_link_vote(self, vote: Vote, dry_run: bool) -> str:
        """Try to link a vote to a bill by fetching from API."""
        # Parse vote_id to get components
        parts = vote.vote_id.split("-")
        if len(parts) != 4:
            return "error"

        chamber, congress, session, roll_call = parts

        # Determine API endpoint
        if chamber == "house":
            chamber_endpoint = "house-vote"
            response_key = "houseRollCallVote"
        else:
            chamber_endpoint = "senate-vote"
            response_key = "senateRollCallVote"

        url = f"{self.CONGRESS_API_BASE}/{chamber_endpoint}/{congress}/{session}/{roll_call}"
        params = {"api_key": self.api_key, "format": "json"}

        try:
            response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stderr.write(f"  Error fetching {vote.vote_id}: {e}")
            return "error"

        vote_detail = data.get(response_key, {})

        # Try to extract bill info from the vote detail
        bill = self._find_or_create_bill(vote_detail, int(congress), dry_run)

        if bill:
            if dry_run:
                self.stdout.write(f"  Would link {vote.vote_id} -> {bill.bill_id}")
            else:
                vote.bill = bill
                vote.save(update_fields=["bill"])
            return "linked"

        return "not_found"

    def _find_or_create_bill(self, vote_detail: dict, congress: int, dry_run: bool) -> Bill | None:
        """Extract bill info from vote detail, find or create matching Bill."""
        leg_type = vote_detail.get("legislationType", "")
        leg_number = vote_detail.get("legislationNumber")

        if not leg_type or not leg_number:
            return None

        # Convert type to lowercase (HR -> hr, S -> s, HJRES -> hjres, etc.)
        bill_type = leg_type.lower().replace(".", "").replace(" ", "")
        bill_id = f"{bill_type}{leg_number}-{congress}"

        # Try to find existing bill
        try:
            return Bill.objects.get(bill_id=bill_id)
        except Bill.DoesNotExist:
            pass

        # Create the bill by fetching from API
        if dry_run:
            self.stdout.write(f"    Would create bill: {bill_id}")
            self.bills_created += 1
            # Return a fake bill for dry run
            return Bill(bill_id=bill_id)

        bill = self._fetch_and_create_bill(bill_type, leg_number, congress)
        if bill:
            self.bills_created += 1
        return bill

    def _fetch_and_create_bill(self, bill_type: str, number: int, congress: int) -> Bill | None:
        """Fetch bill details from API and create Bill record."""
        url = f"{self.CONGRESS_API_BASE}/bill/{congress}/{bill_type}/{number}"
        params = {"api_key": self.api_key, "format": "json"}

        try:
            time.sleep(0.3)  # Rate limiting
            response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stderr.write(f"    Error fetching bill {bill_type}{number}-{congress}: {e}")
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
                    latest_action_date = datetime.strptime(action_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            latest_action_text = latest_action.get("text", "")

        # Build display number
        type_display = {
            "hr": "H.R.",
            "s": "S.",
            "hjres": "H.J.Res.",
            "sjres": "S.J.Res.",
            "hconres": "H.Con.Res.",
            "sconres": "S.Con.Res.",
            "hres": "H.Res.",
            "sres": "S.Res.",
        }
        display_number = f"{type_display.get(bill_type, bill_type.upper())} {number}"

        # Create bill
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
