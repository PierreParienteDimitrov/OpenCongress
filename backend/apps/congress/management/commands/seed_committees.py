"""
Seed committees from unitedstates/congress-legislators GitHub data.

Uses:
- committees-current.yaml  — committee definitions (name, type, subcommittees)
- committee-membership-current.yaml — member assignments (bioguide, role, rank)

Usage:
    python manage.py seed_committees
"""

import requests
import yaml
from django.core.management.base import BaseCommand

from apps.congress.models import Committee, CommitteeMember, Member

# GitHub raw URLs for the unitedstates/congress-legislators data
COMMITTEES_YAML = (
    "https://raw.githubusercontent.com/unitedstates/"
    "congress-legislators/main/committees-current.yaml"
)
MEMBERSHIP_YAML = (
    "https://raw.githubusercontent.com/unitedstates/"
    "congress-legislators/main/committee-membership-current.yaml"
)


class Command(BaseCommand):
    help = "Seed committees from unitedstates/congress-legislators GitHub data"

    def handle(self, *args, **options):
        self.stdout.write("Fetching committee definitions...")
        committees_data = self._fetch_yaml(COMMITTEES_YAML)
        if not committees_data:
            self.stderr.write(self.style.ERROR("Failed to fetch committee data"))
            return

        self.stdout.write("Fetching committee membership...")
        membership_data = self._fetch_yaml(MEMBERSHIP_YAML)
        if not membership_data:
            self.stderr.write(self.style.ERROR("Failed to fetch membership data"))
            return

        # Clear existing committee members to avoid stale data
        deleted_count, _ = CommitteeMember.objects.all().delete()
        if deleted_count:
            self.stdout.write(f"Cleared {deleted_count} existing member assignments")

        # Process committee definitions
        self._process_committees(committees_data, membership_data)

        # Summary
        total_committees = Committee.objects.count()
        top_level = Committee.objects.filter(parent_committee__isnull=True).count()
        subcommittees = Committee.objects.filter(parent_committee__isnull=False).count()
        total_assignments = CommitteeMember.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! {total_committees} committees "
                f"({top_level} top-level, {subcommittees} subcommittees), "
                f"{total_assignments} member assignments"
            )
        )

    def _fetch_yaml(self, url: str) -> list | dict | None:
        """Fetch and parse a YAML file from GitHub."""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return yaml.safe_load(response.text)
        except Exception as e:
            self.stderr.write(f"Error fetching {url}: {e}")
            return None

    def _thomas_to_system_code(self, thomas_id: str) -> str:
        """Convert thomas_id (e.g. 'HSAG') to Congress.gov system code ('hsag00')."""
        return thomas_id.lower() + "00"

    def _sub_system_code(self, thomas_id: str, sub_thomas_id: str) -> str:
        """Build subcommittee system code from parent thomas_id and sub thomas_id.

        e.g. thomas_id='HSAG', sub_thomas_id='15' -> 'hsag15'
        """
        return thomas_id.lower() + sub_thomas_id.zfill(2)

    def _membership_key_to_system_code(self, key: str) -> str:
        """Convert membership YAML key to system code.

        e.g. 'SSAF' -> 'ssaf00', 'SSAF13' -> 'ssaf13'
        """
        # Keys like 'SSAF' (4 chars = top-level) or 'SSAF13' (>4 chars = subcommittee)
        # But some top-level keys are also longer (e.g. 'JSPR', 'JSLC')
        # The pattern: first 4 chars are the parent thomas_id, rest is sub thomas_id
        # For top-level, there's no suffix after the 4-char prefix
        # Actually, top-level keys are exactly 4 chars, subcommittee keys are longer
        if len(key) <= 4:
            return key.lower() + "00"
        parent_code = key[:4].lower()
        sub_code = key[4:]
        return parent_code + sub_code.zfill(2)

    def _detect_chamber(self, committee_type: str) -> str:
        """Map committee type from YAML to chamber."""
        if committee_type == "house":
            return "house"
        elif committee_type == "senate":
            return "senate"
        elif committee_type == "joint":
            return "joint"
        return "house"  # Fallback

    def _detect_committee_type(self, committee_data: dict) -> str:
        """Detect CommitteeType from YAML data."""
        yaml_type = committee_data.get("type", "")
        if yaml_type == "joint":
            return Committee.CommitteeType.JOINT
        if yaml_type == "select":
            return Committee.CommitteeType.SELECT
        return Committee.CommitteeType.STANDING

    def _process_committees(self, committees_data: list, membership_data: dict) -> None:
        """Process all committee definitions and their memberships."""
        # Build a set of valid member bioguide IDs for fast lookup
        valid_bioguides = set(Member.objects.values_list("bioguide_id", flat=True))
        self.stdout.write(f"Found {len(valid_bioguides)} members in database")

        for comm_data in committees_data:
            thomas_id = comm_data.get("thomas_id", "")
            name = comm_data.get("name", "")
            if not thomas_id or not name:
                continue

            system_code = self._thomas_to_system_code(thomas_id)
            chamber = self._detect_chamber(comm_data.get("type", ""))
            committee_type = self._detect_committee_type(comm_data)
            url = comm_data.get("url", "")

            # Create/update top-level committee
            committee, created = Committee.objects.update_or_create(
                committee_id=system_code,
                defaults={
                    "name": name,
                    "chamber": chamber,
                    "committee_type": committee_type,
                    "url": url,
                    "parent_committee": None,
                },
            )

            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action}: {name} ({system_code})")

            # Process members for this committee
            membership_key = thomas_id
            if membership_key in membership_data:
                member_count = self._process_members(
                    committee,
                    membership_data[membership_key],
                    valid_bioguides,
                )
                if member_count > 0:
                    self.stdout.write(f"    {member_count} members")

            # Process subcommittees
            for sub_data in comm_data.get("subcommittees", []):
                sub_thomas_id = sub_data.get("thomas_id", "")
                sub_name = sub_data.get("name", "")
                if not sub_thomas_id or not sub_name:
                    continue

                sub_system_code = self._sub_system_code(thomas_id, sub_thomas_id)

                sub_committee, sub_created = Committee.objects.update_or_create(
                    committee_id=sub_system_code,
                    defaults={
                        "name": sub_name,
                        "chamber": chamber,
                        "committee_type": Committee.CommitteeType.SUBCOMMITTEE,
                        "parent_committee": committee,
                        "url": "",
                    },
                )

                sub_action = "Created" if sub_created else "Updated"
                self.stdout.write(
                    f"    {sub_action} subcommittee: {sub_name} ({sub_system_code})"
                )

                # Process subcommittee members
                sub_membership_key = thomas_id + sub_thomas_id
                if sub_membership_key in membership_data:
                    sub_member_count = self._process_members(
                        sub_committee,
                        membership_data[sub_membership_key],
                        valid_bioguides,
                    )
                    if sub_member_count > 0:
                        self.stdout.write(f"      {sub_member_count} members")

    def _process_members(
        self,
        committee: Committee,
        members_list: list,
        valid_bioguides: set,
    ) -> int:
        """Process and save committee members from membership YAML."""
        member_count = 0

        for member_data in members_list:
            bioguide_id = member_data.get("bioguide", "")
            if not bioguide_id or bioguide_id not in valid_bioguides:
                continue

            # Determine role from title
            title = member_data.get("title", "").lower()
            if "chairman" in title or "chairwoman" in title or title == "chair":
                role = CommitteeMember.Role.CHAIR
            elif "ranking" in title:
                role = CommitteeMember.Role.RANKING
            else:
                role = CommitteeMember.Role.MEMBER

            CommitteeMember.objects.update_or_create(
                committee=committee,
                member_id=bioguide_id,
                defaults={"role": role},
            )
            member_count += 1

        return member_count
