"""
Seed committee hearings from Congress.gov API.

Usage:
    python manage.py seed_hearings --congress=119
"""

import os
import time
from datetime import datetime

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Bill, Committee, Hearing, HearingWitness

CONGRESS_API_BASE = "https://api.congress.gov/v3"


class Command(BaseCommand):
    help = "Seed committee hearings from Congress.gov API"

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
            default=250,
            help="Maximum number of hearings to fetch (default: 250)",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Starting offset for pagination",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            self.stderr.write(
                self.style.ERROR("CONGRESS_API_KEY not set in environment")
            )
            return

        congress = options["congress"]
        limit = options["limit"]
        start_offset = options["offset"]

        # Pre-load committee lookup
        self._committee_cache = {}
        for c in Committee.objects.all():
            self._committee_cache[c.committee_id.lower()] = c
            # Also cache by name prefix for fuzzy matching
            name_key = c.name.lower().strip()
            self._committee_cache[name_key] = c

        created = 0
        updated = 0
        offset = start_offset

        self.stdout.write(
            f"Fetching hearings for Congress {congress} (limit {limit})..."
        )

        while created + updated < limit:
            url = f"{CONGRESS_API_BASE}/hearing/{congress}"
            params = {
                "api_key": api_key,
                "limit": min(limit - (created + updated), 50),
                "offset": offset,
                "format": "json",
            }

            data = None
            for attempt in range(3):
                try:
                    time.sleep(0.3 if attempt == 0 else 2.0)
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    break
                except Exception as e:
                    if attempt == 2:
                        self.stderr.write(
                            f"  Failed to fetch hearings at offset {offset}: {e}"
                        )

            if data is None:
                break

            hearings = data.get("hearings", [])
            if not hearings:
                break

            for hearing_data in hearings:
                if created + updated >= limit:
                    break

                was_created = self._process_hearing(api_key, hearing_data, congress)
                if was_created:
                    created += 1
                else:
                    updated += 1

            total = created + updated
            self.stdout.write(f"  Processed {total} hearings...")

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += len(hearings)

        self.stdout.write(
            self.style.SUCCESS(f"Done! Created {created}, updated {updated}")
        )

    def _process_hearing(self, api_key: str, hearing_data: dict, congress: int) -> bool:
        """Process a single hearing. Returns True if created."""
        number = hearing_data.get("number")
        part = hearing_data.get("part", 1) or 1
        chamber = hearing_data.get("chamber", "").lower()
        if chamber == "house of representatives":
            chamber = "house"

        hearing_id = f"hearing-{congress}-{chamber}-{number}-{part}"

        # Fetch detail
        detail_url = hearing_data.get("url", "")
        if not detail_url:
            detail_url = f"{CONGRESS_API_BASE}/hearing/{congress}/{chamber}/{number}"

        detail = None
        for attempt in range(3):
            try:
                time.sleep(0.3 if attempt == 0 else 2.0)
                params = {"api_key": api_key, "format": "json"}
                response = requests.get(detail_url, params=params, timeout=30)
                response.raise_for_status()
                detail = response.json().get("hearing", {})
                break
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(f"  Failed to fetch hearing {hearing_id}: {e}")

        if detail is None:
            detail = hearing_data

        title = detail.get("title", hearing_data.get("title", ""))
        if not title:
            return False

        # Parse date
        hearing_date = None
        date_str = detail.get("dates", [{}])
        if isinstance(date_str, list) and date_str:
            first_date = date_str[0]
            if isinstance(first_date, dict):
                first_date = first_date.get("date", "")
            if first_date:
                try:
                    hearing_date = datetime.fromisoformat(
                        first_date.replace("Z", "+00:00")
                    )
                except ValueError:
                    try:
                        hearing_date = datetime.strptime(first_date[:10], "%Y-%m-%d")
                    except ValueError:
                        pass

        # Find committee
        committee = None
        committees_data = detail.get("committees", [])
        if committees_data:
            for cd in committees_data:
                sys_code = cd.get("systemCode", "")
                if sys_code:
                    committee = self._committee_cache.get(sys_code.lower())
                    if committee:
                        break
                name = cd.get("name", "")
                if name:
                    committee = self._committee_cache.get(name.lower().strip())
                    if committee:
                        break

        # Find related bill
        bill = None
        associated = detail.get("associatedBills", []) or detail.get(
            "associatedLegislation", []
        )
        if associated:
            for ab in associated:
                bill_number = ab.get("number")
                bill_type = ab.get("type", "").lower()
                if bill_number and bill_type:
                    bill_id = f"{bill_type}{bill_number}-{congress}"
                    try:
                        bill = Bill.objects.get(bill_id=bill_id)
                        break
                    except Bill.DoesNotExist:
                        pass

        # Convert API URL to human-readable congress.gov URL
        congress_url = f"https://www.congress.gov/event/{congress}th-congress/hearings"

        defaults = {
            "committee": committee,
            "chamber": chamber if chamber in ("house", "senate") else "house",
            "congress": congress,
            "title": title,
            "date": hearing_date,
            "location": detail.get("location", ""),
            "hearing_type": detail.get("type", ""),
            "bill": bill,
            "url": congress_url,
        }

        _, was_created = Hearing.objects.update_or_create(
            hearing_id=hearing_id,
            defaults=defaults,
        )

        # Process witnesses if available
        witnesses = detail.get("witnesses", [])
        if witnesses and was_created:
            for w in witnesses:
                name = w.get("name", "")
                if not name:
                    continue
                HearingWitness.objects.get_or_create(
                    hearing_id=hearing_id,
                    name=name,
                    defaults={
                        "position": w.get("position", ""),
                        "organization": w.get("organization", ""),
                    },
                )

        return was_created
