"""
Seed members from Congress.gov API.

Usage:
    python manage.py seed_members
"""

import os
import time

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Member


class Command(BaseCommand):
    help = "Seed members from Congress.gov API"

    CONGRESS_API_BASE = "https://api.congress.gov/v3"
    SOCIAL_MEDIA_URL = (
        "https://theunitedstates.io/congress-legislators/legislators-social-media.json"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=250,
            help="Number of members to fetch per page (max 250)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            self.stderr.write(
                self.style.ERROR("CONGRESS_API_KEY not set in environment")
            )
            return

        self.stdout.write("Fetching current members from Congress.gov...")

        members_data = self._fetch_all_members(api_key, options["limit"])
        self.stdout.write(f"Found {len(members_data)} members")

        # Fetch social media data
        self.stdout.write("Fetching social media data...")
        social_media = self._fetch_social_media()
        self.stdout.write(f"Found social media for {len(social_media)} members")

        # Create or update members
        created = 0
        updated = 0

        for member_data in members_data:
            bioguide_id = member_data.get("bioguideId")
            if not bioguide_id:
                continue

            # Get social media for this member
            social = social_media.get(bioguide_id, {})

            # Determine chamber and district
            terms = member_data.get("terms", {}).get("item", [])
            current_term = terms[-1] if terms else {}
            chamber = current_term.get("chamber", "").lower()
            if chamber == "house of representatives":
                chamber = "house"

            # Extract district from member data (top-level field in Congress API)
            # At-large districts (single-rep states/territories) have no district field
            district = member_data.get("district")
            if district is None and chamber == "house":
                district = 0

            defaults = {
                "full_name": member_data.get("name", ""),
                "first_name": member_data.get("firstName", ""),
                "last_name": member_data.get("lastName", ""),
                "nickname": member_data.get("nickName", "") or "",
                "party": self._map_party(member_data.get("partyName", "")),
                "chamber": chamber if chamber in ["house", "senate"] else "house",
                "state": member_data.get("state", ""),
                "district": district,
                "photo_url": member_data.get("depiction", {}).get("imageUrl", "") or "",
                "twitter_handle": social.get("twitter", ""),
                "facebook_id": social.get("facebook", ""),
                "youtube_id": social.get("youtube_id", ""),
                "is_active": True,
            }

            member, was_created = Member.objects.update_or_create(
                bioguide_id=bioguide_id,
                defaults=defaults,
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} members, updated {updated} members")
        )

    def _fetch_all_members(self, api_key: str, limit: int) -> list:
        """Fetch all current members with pagination."""
        members = []
        offset = 0

        while True:
            url = f"{self.CONGRESS_API_BASE}/member"
            params = {
                "api_key": api_key,
                "currentMember": "true",
                "limit": limit,
                "offset": offset,
                "format": "json",
            }

            response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()

            batch = data.get("members", [])
            members.extend(batch)

            self.stdout.write(f"  Fetched {len(members)} members so far...")

            # Check if there are more pages
            pagination = data.get("pagination", {})
            if pagination.get("next") is None or len(batch) < limit:
                break

            offset += limit
            time.sleep(0.5)  # Rate limiting

        return members

    def _fetch_social_media(self) -> dict:
        """Fetch social media data from theunitedstates.io."""
        try:
            response = requests.get(self.SOCIAL_MEDIA_URL, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Index by bioguide_id
            return {
                item["id"]["bioguide"]: {
                    "twitter": item.get("social", {}).get("twitter", ""),
                    "facebook": item.get("social", {}).get("facebook", ""),
                    "youtube_id": item.get("social", {}).get("youtube_id", ""),
                }
                for item in data
                if "id" in item and "bioguide" in item["id"]
            }
        except Exception as e:
            self.stderr.write(f"Failed to fetch social media: {e}")
            return {}

    def _map_party(self, party_name: str) -> str:
        """Map party name to single-letter code."""
        party_map = {
            "Democratic": "D",
            "Republican": "R",
            "Independent": "I",
            "Libertarian": "I",
        }
        return party_map.get(party_name, "I")
