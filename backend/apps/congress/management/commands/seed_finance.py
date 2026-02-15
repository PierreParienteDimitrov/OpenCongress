"""
Seed campaign finance data from FEC OpenFEC API.

Usage:
    python manage.py seed_finance --cycle=2026
"""

import os
import time

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import (
    CandidateFinance,
    Member,
    TopContributor,
)

FEC_API_BASE = "https://api.open.fec.gov/v1"


class Command(BaseCommand):
    help = "Seed campaign finance data from FEC OpenFEC API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cycle",
            type=int,
            default=2026,
            help="Election cycle year (default: 2026)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of members to process (0 = all)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("FEC_API_KEY")
        if not api_key:
            self.stderr.write(
                self.style.ERROR(
                    "FEC_API_KEY not set. Get a free key at https://api.data.gov/signup/"
                )
            )
            return

        cycle = options["cycle"]
        limit = options["limit"]

        members = Member.objects.filter(is_active=True).order_by("last_name")
        if limit:
            members = members[:limit]

        total = members.count()
        created = 0
        updated = 0
        skipped = 0

        self.stdout.write(
            f"Fetching finance data for {total} members (cycle {cycle})..."
        )

        for i, member in enumerate(members, 1):
            result = self._process_member(api_key, member, cycle)
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
            else:
                skipped += 1

            if i % 25 == 0:
                self.stdout.write(f"  Processed {i}/{total} members...")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {created}, updated {updated}, skipped {skipped}"
            )
        )

    def _process_member(self, api_key: str, member: Member, cycle: int) -> str:
        """Fetch and store finance data for a single member."""
        # Step 1: Find FEC candidate ID by name + state
        candidate = self._find_fec_candidate(api_key, member)
        if not candidate:
            return "skipped"

        fec_id = candidate.get("candidate_id", "")
        if not fec_id:
            return "skipped"

        # Step 2: Get financial totals for this cycle
        totals = self._fetch_candidate_totals(api_key, fec_id, cycle)
        if not totals:
            return "skipped"

        # Step 3: Create/update finance record
        defaults = {
            "fec_candidate_id": fec_id,
            "total_receipts": totals.get("receipts", 0) or 0,
            "total_disbursements": totals.get("disbursements", 0) or 0,
            "cash_on_hand": totals.get("cash_on_hand_end_period", 0) or 0,
            "total_individual_contributions": totals.get("individual_contributions", 0)
            or 0,
            "total_pac_contributions": totals.get(
                "other_political_committee_contributions", 0
            )
            or 0,
            "total_party_contributions": totals.get(
                "political_party_committee_contributions", 0
            )
            or 0,
            "candidate_self_contributions": totals.get("candidate_contribution", 0)
            or 0,
        }

        record, was_created = CandidateFinance.objects.update_or_create(
            member=member,
            election_cycle=cycle,
            defaults=defaults,
        )

        # Step 4: Fetch top contributors (committee-level aggregation)
        self._fetch_top_contributors(api_key, fec_id, cycle, record)

        return "created" if was_created else "updated"

    def _find_fec_candidate(self, api_key: str, member: Member) -> dict | None:
        """Find the FEC candidate record matching this member."""
        url = f"{FEC_API_BASE}/candidates/search/"
        params = {
            "api_key": api_key,
            "name": f"{member.last_name}, {member.first_name}",
            "state": member.state,
            "office": "H" if member.chamber == "house" else "S",
            "is_active_candidate": "true",
            "per_page": 5,
        }

        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt == 0 else 2.0)
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                if results:
                    return results[0]
                return None
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(
                        f"  Failed to find FEC candidate for {member.full_name}: {e}"
                    )
        return None

    def _fetch_candidate_totals(
        self, api_key: str, fec_id: str, cycle: int
    ) -> dict | None:
        """Fetch candidate financial totals for a specific cycle."""
        url = f"{FEC_API_BASE}/candidate/{fec_id}/totals/"
        params = {
            "api_key": api_key,
            "cycle": cycle,
            "per_page": 1,
        }

        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt == 0 else 2.0)
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                if results:
                    return results[0]
                return None
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(f"  Failed to fetch totals for {fec_id}: {e}")
        return None

    def _fetch_top_contributors(
        self, api_key: str, fec_id: str, cycle: int, record: CandidateFinance
    ):
        """Fetch top contributing committees/organizations."""
        # Use the schedules/schedule_a/by_employer endpoint for employer aggregation
        url = f"{FEC_API_BASE}/schedules/schedule_a/by_employer/"
        params = {
            "api_key": api_key,
            "candidate_id": fec_id,
            "cycle": cycle,
            "sort": "-total",
            "per_page": 20,
        }

        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt == 0 else 2.0)
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])

                # Clear old contributors and replace
                record.top_contributors.all().delete()

                for item in results:
                    employer = item.get("employer", "")
                    if not employer or employer.upper() in (
                        "NOT EMPLOYED",
                        "RETIRED",
                        "NONE",
                        "N/A",
                        "SELF-EMPLOYED",
                        "SELF",
                    ):
                        continue

                    TopContributor.objects.create(
                        finance_record=record,
                        contributor_name=employer,
                        total_amount=item.get("total", 0) or 0,
                        contributor_type="employer",
                    )
                break
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(
                        f"  Failed to fetch contributors for {fec_id}: {e}"
                    )
