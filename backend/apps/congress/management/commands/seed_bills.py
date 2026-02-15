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

from apps.congress.models import Bill, BillCommittee, Committee, Member


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
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Starting offset for API pagination (skip already-fetched bills)",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            default=False,
            help="Skip bills that already exist in the DB (only fetch new ones)",
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
        bill_type = options["type"]
        start_offset = options["offset"]
        self.skip_existing = options["skip_existing"]

        if bill_type:
            bill_types = [bill_type]
        else:
            # Fetch major bill types
            bill_types = ["hr", "s"]

        # Pre-load existing bill IDs for fast lookup when skipping
        if self.skip_existing:
            self._existing_bill_ids = set(
                Bill.objects.filter(congress=congress).values_list("bill_id", flat=True)
            )
            self.stdout.write(
                f"Skip-existing mode: {len(self._existing_bill_ids)} bills already in DB"
            )
        else:
            self._existing_bill_ids = set()

        total_created = 0
        total_updated = 0
        total_skipped = 0

        for bt in bill_types:
            self.stdout.write(f"Fetching {bt.upper()} bills for Congress {congress}...")
            created, updated, skipped = self._fetch_bills(
                api_key, congress, bt, limit // len(bill_types), start_offset
            )
            total_created += created
            total_updated += updated
            total_skipped += skipped

        msg = f"Done! Created {total_created} bills, updated {total_updated} bills"
        if total_skipped:
            msg += f", skipped {total_skipped} existing bills"
        self.stdout.write(self.style.SUCCESS(msg))

    def _fetch_bills(
        self,
        api_key: str,
        congress: int,
        bill_type: str,
        limit: int,
        start_offset: int = 0,
    ) -> tuple[int, int, int]:
        """Fetch bills of a specific type. Returns (created, updated, skipped)."""
        url = f"{self.CONGRESS_API_BASE}/bill/{congress}/{bill_type}"
        params = {
            "api_key": api_key,
            "limit": min(limit, 50),
            "format": "json",
        }

        created = 0
        updated = 0
        skipped = 0
        offset = start_offset

        if start_offset:
            self.stdout.write(f"  Starting from offset {start_offset}...")

        while created + updated + skipped < limit:
            params["offset"] = offset

            # Retry up to 3 times for transient failures
            data = None
            for attempt in range(3):
                try:
                    time.sleep(0.3 if attempt == 0 else 2.0)
                    response = requests.get(url, params=params, timeout=(10, 30))  # type: ignore[arg-type]
                    response.raise_for_status()
                    data = response.json()
                    break
                except Exception as e:
                    if attempt == 2:
                        self.stderr.write(
                            f"  Failed to fetch page at offset {offset} after 3 attempts: {e}"
                        )

            if data is None:
                break

            bills = data.get("bills", [])
            if not bills:
                break

            for bill_data in bills:
                if created + updated + skipped >= limit:
                    break

                number = bill_data.get("number")
                if not number:
                    continue

                bill_id = f"{bill_type}{number}-{congress}"

                # Skip existing bills without making detail API calls
                if self.skip_existing and bill_id in self._existing_bill_ids:
                    skipped += 1
                    continue

                was_created = self._process_bill(
                    api_key, bill_data, congress, bill_type
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

            total = created + updated + skipped
            self.stdout.write(
                f"  Processed {total} {bill_type.upper()} bills..."
                + (f" (skipped {skipped})" if skipped else "")
            )

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += len(bills)

        return created, updated, skipped

    def _process_bill(
        self, api_key: str, bill_data: dict, congress: int, bill_type: str
    ) -> bool:
        """Process a single bill. Returns True if created, False if updated."""
        number = bill_data.get("number")
        if not number:
            return False

        bill_id = f"{bill_type}{number}-{congress}"

        # Fetch bill details with retry
        detail_url = f"{self.CONGRESS_API_BASE}/bill/{congress}/{bill_type}/{number}"
        params = {"api_key": api_key, "format": "json"}

        detail = None
        for attempt in range(3):
            try:
                time.sleep(0.3 if attempt == 0 else 2.0)
                response = requests.get(detail_url, params=params, timeout=(10, 30))  # type: ignore[arg-type]
                response.raise_for_status()
                detail = response.json().get("bill", {})
                break
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(
                        f"  Failed to fetch bill {bill_id} after 3 attempts: {e}"
                    )

        if detail is None:
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

        bill_obj, was_created = Bill.objects.update_or_create(
            bill_id=bill_id,
            defaults=defaults,
        )

        # Link bill to committees
        self._link_bill_committees(bill_obj, detail)

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

        for attempt in range(3):
            try:
                time.sleep(0.3 if attempt == 0 else 2.0)
                response = requests.get(url, params=params, timeout=(10, 30))  # type: ignore[arg-type]
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
                break
            except Exception:
                if attempt == 2:
                    pass  # Summary is optional

    def _link_bill_committees(self, bill: Bill, detail: dict):
        """Link a bill to its referred committees from the API response."""
        committees_data = detail.get("committees", {})

        # Congress.gov nests committees under a "url" key or returns a list;
        # the actual committee items may be in a "committees" sub-key
        # or at the top level depending on the endpoint response format.
        # We handle both cases.
        if isinstance(committees_data, dict):
            # Sometimes the detail response has committees as
            # {"count": N, "url": "..."} - we'd need a separate call.
            # Skip if no inline committee data.
            return

        if not isinstance(committees_data, list):
            return

        # Parse referred date from actions
        referred_date = None
        actions = detail.get("actions", {})
        if isinstance(actions, dict):
            actions = actions.get("actions", [])
        if isinstance(actions, list):
            for action_item in actions:
                text = action_item.get("text", "")
                if "Referred to" in text and action_item.get("actionDate"):
                    try:
                        from datetime import datetime

                        referred_date = datetime.strptime(
                            action_item["actionDate"][:10], "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        pass
                    break

        linked = 0
        for comm_item in committees_data:
            system_code = comm_item.get("systemCode", "")
            if not system_code:
                continue

            try:
                committee = Committee.objects.get(committee_id=system_code)
                BillCommittee.objects.update_or_create(
                    bill=bill,
                    committee=committee,
                    defaults={"referred_date": referred_date},
                )
                linked += 1
            except Committee.DoesNotExist:
                continue

        if linked > 0:
            self.stdout.write(
                f"    Linked {bill.display_number} to {linked} committee(s)"
            )
