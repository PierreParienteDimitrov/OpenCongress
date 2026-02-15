"""
Seed industry contribution data from the FEC OpenFEC API.

Fetches top occupations for each member's principal campaign committee,
maps them to industry categories, and saves as IndustryContribution records.

Prerequisite: CandidateFinance records must already exist (run seed_finance first).

Usage:
    python manage.py seed_industry_contributions --cycle=2026
    python manage.py seed_industry_contributions --cycle=2026 --limit=50
    python manage.py seed_industry_contributions --cycle=2026 --chamber=senate
"""

import os
import time
from collections import defaultdict
from decimal import Decimal

import requests
from django.core.management.base import BaseCommand

from apps.congress.industry_mapping import map_occupation_to_industry
from apps.congress.models import CandidateFinance, IndustryContribution

FEC_API_BASE = "https://api.open.fec.gov/v1"


class Command(BaseCommand):
    help = "Seed industry contribution data from the FEC OpenFEC API"

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
            help="Max CandidateFinance records to process (0 = all)",
        )
        parser.add_argument(
            "--chamber",
            type=str,
            choices=["house", "senate"],
            default=None,
            help="Only fetch for one chamber",
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
        chamber = options["chamber"]

        cf_qs = CandidateFinance.objects.filter(
            cycle=cycle,
            fec_candidate_id__gt="",
        ).select_related("member")

        if chamber:
            cf_qs = cf_qs.filter(member__chamber=chamber)

        cf_records = list(cf_qs.order_by("member__last_name"))
        if limit:
            cf_records = cf_records[:limit]

        if not cf_records:
            self.stderr.write(
                self.style.WARNING(
                    f"No CandidateFinance records found for cycle {cycle}. "
                    f"Run seed_finance first."
                )
            )
            return

        self.stdout.write(
            f"Fetching industry contributions for {len(cf_records)} members, "
            f"cycle {cycle}..."
        )

        success = 0
        skipped = 0

        for i, cf in enumerate(cf_records):
            if i > 0 and i % 25 == 0:
                self.stdout.write(f"  Processed {i}/{len(cf_records)} members...")

            result = self._process_candidate(api_key, cf, cycle)
            if result:
                success += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done! Populated {success}, skipped {skipped} members")
        )

    def _process_candidate(
        self, api_key: str, cf: CandidateFinance, cycle: int
    ) -> bool:
        """Fetch occupations, map to industries, save IndustryContributions."""
        committee_id = self._find_principal_committee(api_key, cf.fec_candidate_id)
        if not committee_id:
            return False

        occupations = self._fetch_occupations(api_key, committee_id, cycle)
        if not occupations:
            return False

        # Map occupations → aggregate by industry
        industry_totals: dict[str, Decimal] = defaultdict(Decimal)
        for occ in occupations:
            occ_name = occ.get("occupation", "") or ""
            amount = Decimal(str(occ.get("total", 0) or 0))
            if amount > 0:
                industry = map_occupation_to_industry(occ_name)
                industry_totals[industry] += amount

        if not industry_totals:
            return False

        # Sort by total descending, keep top 15
        sorted_industries = sorted(
            industry_totals.items(), key=lambda x: x[1], reverse=True
        )

        IndustryContribution.objects.filter(candidate_finance=cf).delete()
        for rank, (industry_name, total) in enumerate(sorted_industries[:15], 1):
            IndustryContribution.objects.create(
                candidate_finance=cf,
                industry_name=industry_name,
                total_amount=total,
                rank=rank,
            )

        return True

    def _find_principal_committee(self, api_key: str, candidate_id: str) -> str | None:
        """Find the principal campaign committee for a candidate."""
        params: dict[str, str | int] = {
            "api_key": api_key,
            "candidate_id": candidate_id,
            "designation": "P",
            "per_page": 1,
        }

        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt == 0 else 2.0)
                response = requests.get(
                    f"{FEC_API_BASE}/candidate/{candidate_id}/committees/",
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                results = response.json().get("results", [])
                if results:
                    return results[0].get("committee_id")
                return None
            except Exception:
                if attempt == 2:
                    self.stderr.write(f"  Failed to find committee for {candidate_id}")
        return None

    def _fetch_occupations(
        self, api_key: str, committee_id: str, cycle: int
    ) -> list[dict]:
        """Fetch top occupations by contribution amount."""
        params: dict[str, str | int] = {
            "api_key": api_key,
            "committee_id": committee_id,
            "cycle": cycle,
            "sort": "-total",
            "per_page": 50,
        }

        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt == 0 else 2.0)
                response = requests.get(
                    f"{FEC_API_BASE}/schedules/schedule_a/by_occupation/",
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                return response.json().get("results", [])
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(
                        f"  Failed to fetch occupations for {committee_id}: {e}"
                    )
        return []
