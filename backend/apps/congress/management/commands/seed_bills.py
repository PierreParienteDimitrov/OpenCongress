"""
Seed bills from Congress.gov API.

Usage:
    python manage.py seed_bills --congress=119 --limit=50
"""

import os
import time
from datetime import datetime

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Bill, Member


class Command(BaseCommand):
    help = "Seed bills from Congress.gov API"

    CONGRESS_API_BASE = "https://api.congress.gov/v3"

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
            default=50,
            help="Number of bills to fetch (default: 50)",
        )
        parser.add_argument(
            "--type",
            type=str,
            choices=["hr", "s", "hjres", "sjres", "hconres", "sconres", "hres", "sres"],
            default=None,
            help="Bill type to fetch (default: all major types)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            self.stderr.write(self.style.ERROR("CONGRESS_API_KEY not set in environment"))
            return

        congress = options["congress"]
        limit = options["limit"]
        bill_type = options["type"]

        if bill_type:
            bill_types = [bill_type]
        else:
            # Fetch major bill types
            bill_types = ["hr", "s"]

        total_created = 0
        total_updated = 0

        for bt in bill_types:
            self.stdout.write(f"Fetching {bt.upper()} bills for Congress {congress}...")
            created, updated = self._fetch_bills(
                api_key, congress, bt, limit // len(bill_types)
            )
            total_created += created
            total_updated += updated

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {total_created} bills, updated {total_updated} bills"
            )
        )

    def _fetch_bills(
        self, api_key: str, congress: int, bill_type: str, limit: int
    ) -> tuple[int, int]:
        """Fetch bills of a specific type."""
        url = f"{self.CONGRESS_API_BASE}/bill/{congress}/{bill_type}"
        params = {
            "api_key": api_key,
            "limit": min(limit, 50),
            "format": "json",
        }

        created = 0
        updated = 0
        offset = 0

        while created + updated < limit:
            params["offset"] = offset
            response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()

            bills = data.get("bills", [])
            if not bills:
                break

            for bill_data in bills:
                if created + updated >= limit:
                    break

                was_created = self._process_bill(api_key, bill_data, congress, bill_type)
                if was_created:
                    created += 1
                else:
                    updated += 1

            self.stdout.write(f"  Processed {created + updated} {bill_type.upper()} bills...")

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += len(bills)
            time.sleep(0.3)

        return created, updated

    def _process_bill(
        self, api_key: str, bill_data: dict, congress: int, bill_type: str
    ) -> bool:
        """Process a single bill. Returns True if created, False if updated."""
        number = bill_data.get("number")
        if not number:
            return False

        bill_id = f"{bill_type}{number}-{congress}"

        # Fetch bill details
        time.sleep(0.3)
        detail_url = f"{self.CONGRESS_API_BASE}/bill/{congress}/{bill_type}/{number}"
        params = {"api_key": api_key, "format": "json"}

        try:
            response = requests.get(detail_url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            detail = response.json().get("bill", {})
        except Exception as e:
            self.stderr.write(f"  Failed to fetch bill {bill_id}: {e}")
            return False

        # Parse dates
        introduced_date = None
        if detail.get("introducedDate"):
            try:
                introduced_date = datetime.strptime(
                    detail["introducedDate"][:10], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        latest_action_date = None
        latest_action = detail.get("latestAction", {})
        if latest_action.get("actionDate"):
            try:
                latest_action_date = datetime.strptime(
                    latest_action["actionDate"][:10], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        # Get sponsor
        sponsor = None
        sponsors = detail.get("sponsors", [])
        if sponsors:
            sponsor_data = sponsors[0]
            bioguide_id = sponsor_data.get("bioguideId")
            if bioguide_id:
                try:
                    sponsor = Member.objects.get(bioguide_id=bioguide_id)
                except Member.DoesNotExist:
                    pass

        # Build display number
        display_number = f"{bill_type.upper()}. {number}"

        defaults = {
            "bill_type": bill_type,
            "number": number,
            "congress": congress,
            "title": detail.get("title", ""),
            "short_title": (detail.get("shortTitle") or "")[:500],
            "display_number": display_number,
            "sponsor": sponsor,
            "introduced_date": introduced_date,
            "latest_action_date": latest_action_date,
            "latest_action_text": latest_action.get("text", ""),
            "congress_url": detail.get("url", ""),
        }

        _, was_created = Bill.objects.update_or_create(
            bill_id=bill_id,
            defaults=defaults,
        )

        # Fetch summary if available
        if was_created:
            self._fetch_bill_summary(api_key, bill_id, congress, bill_type, number)

        return was_created

    def _fetch_bill_summary(
        self,
        api_key: str,
        bill_id: str,
        congress: int,
        bill_type: str,
        number: int,
    ):
        """Fetch and save bill summary."""
        url = f"{self.CONGRESS_API_BASE}/bill/{congress}/{bill_type}/{number}/summaries"
        params = {"api_key": api_key, "format": "json"}

        try:
            time.sleep(0.3)
            response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()

            summaries = data.get("summaries", [])
            if summaries:
                # Get the most recent summary
                latest = summaries[-1]
                Bill.objects.filter(bill_id=bill_id).update(
                    summary_text=latest.get("text", ""),
                    summary_html=latest.get("text", ""),
                )
        except Exception:
            pass  # Summary is optional
