"""
Seed campaign finance data from the FEC OpenFEC API.

Fetches financial summaries and top contributors for all current members
of Congress using the FEC API (api.open.fec.gov).

Usage:
    python manage.py seed_finance --cycle=2024
    python manage.py seed_finance --cycle=2026 --limit=50
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
    help = "Seed campaign finance data from the FEC OpenFEC API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cycle",
            type=int,
            default=2026,
            help="Election cycle year (default: 2026)",
        )
        parser.add_argument(
            "--fallback-cycle",
            type=int,
            default=0,
            help="Fallback cycle if no totals found for primary cycle (e.g. 2024)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max members to process (0 = all)",
        )
        parser.add_argument(
            "--chamber",
            type=str,
            choices=["house", "senate"],
            default=None,
            help="Only fetch for one chamber",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print detailed skip reasons",
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
        fallback_cycle = options["fallback_cycle"]
        limit = options["limit"]
        chamber = options["chamber"]
        self.verbose = options["verbose"]

        members_qs = Member.objects.filter(is_active=True)
        if chamber:
            members_qs = members_qs.filter(chamber=chamber)

        members = list(members_qs.order_by("last_name"))
        if limit:
            members = members[:limit]

        self.stdout.write(
            f"Fetching finance data for {len(members)} members, cycle {cycle}..."
        )
        if fallback_cycle:
            self.stdout.write(f"  Fallback cycle: {fallback_cycle}")

        created = 0
        updated = 0
        skipped = 0
        skip_no_candidate = 0
        skip_no_totals = 0

        for i, member in enumerate(members):
            if i > 0 and i % 25 == 0:
                self.stdout.write(f"  Processed {i}/{len(members)} members...")

            result = self._process_member(api_key, member, cycle, fallback_cycle)
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
            elif result == "skip_no_candidate":
                skip_no_candidate += 1
                skipped += 1
            elif result == "skip_no_totals":
                skip_no_totals += 1
                skipped += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {created}, updated {updated}, "
                f"skipped {skipped} members"
            )
        )
        if skipped > 0:
            self.stdout.write(
                f"  Skip reasons: {skip_no_candidate} not found in FEC, "
                f"{skip_no_totals} no financial totals for cycle"
            )

    def _process_member(
        self, api_key: str, member: Member, cycle: int, fallback_cycle: int = 0
    ) -> str:
        """Fetch FEC data for a single member.

        Returns 'created', 'updated', 'skip_no_candidate', or 'skip_no_totals'.
        """
        # Step 1: Find FEC candidate ID
        candidate_id = self._find_fec_candidate(api_key, member)
        if not candidate_id:
            if self.verbose:
                self.stderr.write(f"  SKIP {member.full_name}: no FEC candidate found")
            return "skip_no_candidate"

        # Step 2: Fetch financial totals
        effective_cycle = cycle
        totals = self._fetch_candidate_totals(api_key, candidate_id, cycle)
        if not totals and fallback_cycle:
            totals = self._fetch_candidate_totals(api_key, candidate_id, fallback_cycle)
            if totals:
                effective_cycle = fallback_cycle
                if self.verbose:
                    self.stdout.write(
                        f"  {member.full_name}: using fallback cycle {fallback_cycle}"
                    )
        if not totals:
            if self.verbose:
                self.stderr.write(
                    f"  SKIP {member.full_name}: no totals for cycle {cycle}"
                    + (f" or {fallback_cycle}" if fallback_cycle else "")
                )
            return "skip_no_totals"

        # Step 3: Save CandidateFinance record
        finance, was_created = CandidateFinance.objects.update_or_create(
            member=member,
            cycle=effective_cycle,
            defaults={
                "fec_candidate_id": candidate_id,
                "total_receipts": totals.get("receipts", 0) or 0,
                "total_disbursements": totals.get("disbursements", 0) or 0,
                "cash_on_hand": totals.get("last_cash_on_hand_end_period", 0) or 0,
                "debt": totals.get("last_debts_owed_by_committee", 0) or 0,
                "individual_contributions": totals.get("individual_contributions", 0)
                or 0,
                "pac_contributions": totals.get(
                    "other_political_committee_contributions", 0
                )
                or 0,
                "small_contributions": totals.get(
                    "individual_unitemized_contributions", 0
                )
                or 0,
                "large_contributions": totals.get(
                    "individual_itemized_contributions", 0
                )
                or 0,
                "coverage_start_date": _parse_date(totals.get("coverage_start_date")),
                "coverage_end_date": _parse_date(totals.get("coverage_end_date")),
            },
        )

        # Step 4: Fetch top contributors (by committee)
        self._fetch_top_contributors(api_key, finance, candidate_id, effective_cycle)

        return "created" if was_created else "updated"

    def _find_fec_candidate(self, api_key: str, member: Member) -> str | None:
        """Search FEC for a candidate matching this member.

        Tries two strategies:
        1. Search with is_active_candidate=true (current filers)
        2. If no result, search without that filter (catches members who
           haven't filed for the new cycle yet)
        """
        office = "H" if member.chamber == "house" else "S"
        state = member.state.upper()

        base_params: dict[str, str | int] = {
            "api_key": api_key,
            "name": f"{member.last_name}, {member.first_name}",
            "state": state,
            "office": office,
            "sort": "-election_years",
            "per_page": 5,
        }

        # Try active candidates first, then fall back to all candidates
        for active_filter in ("true", None):
            params = {**base_params}
            if active_filter:
                params["is_active_candidate"] = active_filter

            for attempt in range(3):
                try:
                    time.sleep(0.5 if attempt == 0 else 2.0)
                    response = requests.get(
                        f"{FEC_API_BASE}/candidates/search/",
                        params=params,
                        timeout=30,
                    )
                    response.raise_for_status()
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        return results[0].get("candidate_id")
                    break  # No results, try next filter
                except Exception as e:
                    if attempt == 2:
                        self.stderr.write(
                            f"  Failed to find FEC candidate for "
                            f"{member.full_name}: {e}"
                        )
                        break  # Move to next filter on final failure

        return None

    def _fetch_candidate_totals(
        self, api_key: str, candidate_id: str, cycle: int
    ) -> dict | None:
        """Fetch financial totals for a candidate."""
        params: dict[str, str | int] = {
            "api_key": api_key,
            "cycle": cycle,
            "per_page": 1,
        }

        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt == 0 else 2.0)
                response = requests.get(
                    f"{FEC_API_BASE}/candidate/{candidate_id}/totals/",
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                if results:
                    return results[0]
                return None
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(
                        f"  Failed to fetch totals for {candidate_id}: {e}"
                    )
        return None

    def _fetch_top_contributors(
        self,
        api_key: str,
        finance: CandidateFinance,
        candidate_id: str,
        cycle: int,
    ) -> None:
        """Fetch and save top contributing committees/organizations."""
        # First find the principal campaign committee
        committee_id = self._find_principal_committee(api_key, candidate_id)
        if not committee_id:
            return

        params: dict[str, str | int] = {
            "api_key": api_key,
            "cycle": cycle,
            "sort": "-total",
            "per_page": 20,
        }

        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt == 0 else 2.0)
                response = requests.get(
                    f"{FEC_API_BASE}/schedules/schedule_a/by_contributor/",
                    params={**params, "committee_id": committee_id},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])

                # Clear existing contributors for this finance record
                TopContributor.objects.filter(candidate_finance=finance).delete()

                for rank, result in enumerate(results, 1):
                    name = result.get("contributor_name", "Unknown")
                    amount = result.get("total", 0) or 0
                    if amount > 0:
                        TopContributor.objects.create(
                            candidate_finance=finance,
                            contributor_name=name,
                            total_amount=amount,
                            rank=rank,
                        )
                break
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(
                        f"  Failed to fetch contributors for " f"{candidate_id}: {e}"
                    )

    def _find_principal_committee(self, api_key: str, candidate_id: str) -> str | None:
        """Find the principal campaign committee for a candidate."""
        params: dict[str, str | int] = {
            "api_key": api_key,
            "candidate_id": candidate_id,
            "designation": "P",  # Principal
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
                data = response.json()
                results = data.get("results", [])
                if results:
                    return results[0].get("committee_id")
                return None
            except Exception:
                if attempt == 2:
                    return None
        return None


def _parse_date(date_str: str | None):
    """Parse ISO date string from FEC API."""
    if not date_str:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        try:
            from datetime import datetime

            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
