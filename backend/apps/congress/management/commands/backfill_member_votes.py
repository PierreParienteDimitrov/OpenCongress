"""
Backfill member votes for votes that have 0 member vote records.

Usage:
    python manage.py backfill_member_votes
"""

import os
import time
import xml.etree.ElementTree as ET

import requests
from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.congress.models import Member, MemberVote, Vote

STATE_ABBREVS = {
    "alabama": "al",
    "alaska": "ak",
    "arizona": "az",
    "arkansas": "ar",
    "california": "ca",
    "colorado": "co",
    "connecticut": "ct",
    "delaware": "de",
    "florida": "fl",
    "georgia": "ga",
    "hawaii": "hi",
    "idaho": "id",
    "illinois": "il",
    "indiana": "in",
    "iowa": "ia",
    "kansas": "ks",
    "kentucky": "ky",
    "louisiana": "la",
    "maine": "me",
    "maryland": "md",
    "massachusetts": "ma",
    "michigan": "mi",
    "minnesota": "mn",
    "mississippi": "ms",
    "missouri": "mo",
    "montana": "mt",
    "nebraska": "ne",
    "nevada": "nv",
    "new hampshire": "nh",
    "new jersey": "nj",
    "new mexico": "nm",
    "new york": "ny",
    "north carolina": "nc",
    "north dakota": "nd",
    "ohio": "oh",
    "oklahoma": "ok",
    "oregon": "or",
    "pennsylvania": "pa",
    "rhode island": "ri",
    "south carolina": "sc",
    "south dakota": "sd",
    "tennessee": "tn",
    "texas": "tx",
    "utah": "ut",
    "vermont": "vt",
    "virginia": "va",
    "washington": "wa",
    "west virginia": "wv",
    "wisconsin": "wi",
    "wyoming": "wy",
    "district of columbia": "dc",
    "puerto rico": "pr",
    "guam": "gu",
    "virgin islands": "vi",
    "american samoa": "as",
    "northern mariana islands": "mp",
}

CONGRESS_API_BASE = "https://api.congress.gov/v3"
SENATE_VOTE_URL = "https://www.senate.gov/legislative/LIS/roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{roll_call:05d}.xml"

POSITIONS_MAP = {
    "yea": "yea",
    "aye": "yea",
    "nay": "nay",
    "no": "nay",
    "present": "present",
    "not voting": "not_voting",
}


class Command(BaseCommand):
    help = "Backfill member votes for votes missing them"

    def handle(self, *args, **options):
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            self.stderr.write(self.style.ERROR("CONGRESS_API_KEY not set"))
            return

        # Find votes with 0 member votes
        votes_missing = (
            Vote.objects.annotate(mv_count=Count("member_votes"))
            .filter(mv_count=0)
            .order_by("date")
        )

        total = votes_missing.count()
        self.stdout.write(f"Found {total} votes with 0 member votes")

        if total == 0:
            return

        # Build senator cache for Senate votes
        self.senator_cache = self._build_senator_cache()

        house_ok = 0
        senate_ok = 0
        errors = 0

        for i, vote in enumerate(votes_missing, 1):
            self.stdout.write(
                f"  [{i}/{total}] {vote.vote_id} ({vote.chamber}, {vote.date})"
            )

            if vote.chamber == "house":
                count = self._backfill_house_vote(api_key, vote)
            elif vote.chamber == "senate":
                count = self._backfill_senate_vote(vote)
            else:
                count = 0

            if count > 0:
                if vote.chamber == "house":
                    house_ok += 1
                else:
                    senate_ok += 1
                self.stdout.write(f"    -> {count} member votes created")
            else:
                errors += 1
                self.stdout.write(self.style.WARNING("    -> 0 member votes"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! House: {house_ok}, Senate: {senate_ok}, Failed: {errors}"
            )
        )

    def _backfill_house_vote(self, api_key: str, vote: Vote) -> int:
        """Fetch member votes from Congress.gov API for a House vote."""
        url = (
            f"{CONGRESS_API_BASE}/house-vote/"
            f"{vote.congress}/{vote.session}/{vote.roll_call}/members"
        )
        params = {"api_key": api_key, "format": "json"}

        for attempt in range(3):
            try:
                time.sleep(1.0 if attempt == 0 else 3.0)
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json().get("houseRollCallVoteMemberVotes", {})
                break
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(f"    API failed after 3 attempts: {e}")
                    return 0

        results = data.get("results", [])
        created = 0

        for member_data in results:
            bioguide_id = member_data.get("bioguideID")
            vote_cast = member_data.get("voteCast", "").lower()
            position = POSITIONS_MAP.get(vote_cast, "not_voting")

            if not bioguide_id:
                continue

            try:
                member = Member.objects.get(bioguide_id=bioguide_id)
                MemberVote.objects.create(vote=vote, member=member, position=position)
                created += 1
            except Member.DoesNotExist:
                pass
            except Exception as e:
                self.stderr.write(f"    Error for {bioguide_id}: {e}")

        return created

    def _backfill_senate_vote(self, vote: Vote) -> int:
        """Fetch member votes from Senate.gov XML for a Senate vote."""
        url = SENATE_VOTE_URL.format(
            congress=vote.congress,
            session=vote.session,
            roll_call=vote.roll_call,
        )

        try:
            time.sleep(1.0)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except Exception as e:
            self.stderr.write(f"    XML fetch failed: {e}")
            return 0

        members_elem = root.find("members")
        if members_elem is None:
            return 0

        created = 0
        for member_elem in members_elem.findall("member"):
            last_name = (member_elem.findtext("last_name") or "").strip()
            first_name = (member_elem.findtext("first_name") or "").strip()
            state = (member_elem.findtext("state") or "").strip()
            vote_cast = (member_elem.findtext("vote_cast") or "").strip().lower()

            position = POSITIONS_MAP.get(vote_cast, "not_voting")
            member = self._find_senator(last_name, first_name, state)

            if member is None:
                continue

            try:
                MemberVote.objects.create(vote=vote, member=member, position=position)
                created += 1
            except Exception as e:
                self.stderr.write(f"    Error for {last_name} ({state}): {e}")

        return created

    def _build_senator_cache(self) -> dict:
        """Build cache for matching senators by last_name + state."""
        cache = {}
        for member in Member.objects.filter(chamber="senate"):
            last_name = member.last_name
            first_name = member.first_name

            if not last_name and member.full_name:
                parts = member.full_name.split(",")
                if parts:
                    last_name = parts[0].strip()
                    if len(parts) > 1:
                        first_parts = parts[1].strip().split()
                        first_name = first_parts[0] if first_parts else ""

            if not last_name:
                continue

            state = member.state.lower()
            state_abbrev = STATE_ABBREVS.get(state, state)

            cache[f"{last_name.lower()}_{state_abbrev}"] = member
            if first_name:
                cache[f"{first_name.lower()}_{last_name.lower()}_{state_abbrev}"] = (
                    member
                )

        self.stdout.write(f"  Senator cache: {len(cache)} entries")
        return cache

    def _find_senator(
        self, last_name: str, first_name: str, state: str
    ) -> Member | None:
        """Find senator in cache with state normalization."""
        state_lower = state.lower()
        state_normalized = STATE_ABBREVS.get(state_lower, state_lower)

        key = f"{last_name.lower()}_{state_normalized}"
        if key in self.senator_cache:
            return self.senator_cache[key]

        full_key = f"{first_name.lower()}_{last_name.lower()}_{state_normalized}"
        if full_key in self.senator_cache:
            return self.senator_cache[full_key]

        return None
