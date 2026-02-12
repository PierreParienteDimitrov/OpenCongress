"""
Seed committees from Congress.gov API.

Usage:
    python manage.py seed_committees
"""

import os
import time

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Committee, CommitteeMember, Member


class Command(BaseCommand):
    help = "Seed committees from Congress.gov API"

    CONGRESS_API_BASE = "https://api.congress.gov/v3"

    def add_arguments(self, parser):
        parser.add_argument(
            "--congress",
            type=int,
            default=119,
            help="Congress number (default: 119)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            self.stderr.write(
                self.style.ERROR("CONGRESS_API_KEY not set in environment")
            )
            return

        congress = options["congress"]

        # Fetch committees for both chambers
        for chamber in ["house", "senate"]:
            self.stdout.write(f"Fetching {chamber} committees...")
            committees = self._fetch_committees(api_key, chamber, congress)
            self.stdout.write(f"Found {len(committees)} {chamber} committees")

            for comm_data in committees:
                self._process_committee(api_key, comm_data, chamber, congress)

        # Summary
        total_committees = Committee.objects.count()
        total_assignments = CommitteeMember.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done! {total_committees} committees, {total_assignments} member assignments"
            )
        )

    def _fetch_committees(self, api_key: str, chamber: str, congress: int) -> list:
        """Fetch committees for a chamber."""
        url = f"{self.CONGRESS_API_BASE}/committee/{chamber}"
        params = {
            "api_key": api_key,
            "limit": 100,
            "format": "json",
        }

        response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
        response.raise_for_status()
        data = response.json()

        return data.get("committees", [])

    def _process_committee(
        self, api_key: str, comm_data: dict, chamber: str, congress: int
    ):
        """Process a single committee and its members."""
        system_code = comm_data.get("systemCode", "")
        name = comm_data.get("name", "")

        if not system_code or not name:
            return

        # Create or update committee
        committee, created = Committee.objects.update_or_create(
            committee_id=system_code,
            defaults={
                "name": name,
                "chamber": chamber,
                "url": comm_data.get("url", ""),
            },
        )

        action = "Created" if created else "Updated"
        self.stdout.write(f"  {action} committee: {name}")

        # Fetch committee details to get members
        time.sleep(0.3)  # Rate limiting
        self._fetch_committee_members(api_key, committee, chamber, congress)

    def _fetch_committee_members(
        self, api_key: str, committee: Committee, chamber: str, congress: int
    ):
        """Fetch and save committee members."""
        url = f"{self.CONGRESS_API_BASE}/committee/{chamber}/{committee.committee_id}"
        params = {
            "api_key": api_key,
            "format": "json",
        }

        try:
            response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stderr.write(f"    Failed to fetch members for {committee.name}: {e}")
            return

        comm_detail = data.get("committee", {})

        # Process current members
        current_members = comm_detail.get("currentMembers", [])
        member_count = 0

        for member_data in current_members:
            bioguide_id = member_data.get("bioguideId")
            if not bioguide_id:
                continue

            try:
                member = Member.objects.get(bioguide_id=bioguide_id)
            except Member.DoesNotExist:
                continue

            # Determine role
            role = "member"
            if member_data.get("isChair"):
                role = "chair"
            elif member_data.get("isRankingMember"):
                role = "ranking"

            CommitteeMember.objects.update_or_create(
                committee=committee,
                member=member,
                defaults={"role": role},
            )
            member_count += 1

        if member_count > 0:
            self.stdout.write(f"    Added {member_count} members")
