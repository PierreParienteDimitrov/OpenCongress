"""
Seed committee hearing data from the Congress.gov API.

Fetches hearings and committee meetings (including witness lists) for the
current Congress using the Congress.gov API v3.

Usage:
    python manage.py seed_hearings --congress=119
    python manage.py seed_hearings --congress=119 --chamber=house --limit=100
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
            "--chamber",
            type=str,
            choices=["house", "senate"],
            default=None,
            help="Only fetch for one chamber",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=250,
            help="Max hearings to fetch per chamber (default: 250)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            self.stderr.write(
                self.style.ERROR("CONGRESS_API_KEY not set in environment")
            )
            return

        congress = options["congress"]
        chamber = options["chamber"]
        limit = options["limit"]

        chambers = [chamber] if chamber else ["house", "senate"]

        total_created = 0
        total_updated = 0

        for ch in chambers:
            self.stdout.write(
                f"Fetching {ch} committee meetings for Congress {congress}..."
            )
            created, updated = self._fetch_committee_meetings(
                api_key, congress, ch, limit
            )
            total_created += created
            total_updated += updated

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {total_created} hearings, updated {total_updated}"
            )
        )

    def _fetch_committee_meetings(
        self, api_key: str, congress: int, chamber: str, limit: int
    ) -> tuple[int, int]:
        """Fetch committee meetings (hearings, markups) for a chamber."""
        url = f"{CONGRESS_API_BASE}/committee-meeting/{congress}/{chamber}"
        params = {
            "api_key": api_key,
            "limit": min(limit, 250),
            "format": "json",
            "offset": 0,
        }

        created = 0
        updated = 0
        fetched = 0

        while fetched < limit:
            data = self._api_get(url, params)
            if data is None:
                break

            meetings = data.get("committeeMeetings", [])
            if not meetings:
                break

            for meeting in meetings:
                if fetched >= limit:
                    break
                result = self._process_meeting(api_key, meeting, congress, chamber)
                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                fetched += 1

            self.stdout.write(f"  Processed {fetched} {chamber} meetings...")

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            params["offset"] = params["offset"] + len(meetings)

        return created, updated

    def _process_meeting(
        self, api_key: str, meeting: dict, congress: int, chamber: str
    ) -> str:
        """Process a single committee meeting. Returns 'created', 'updated', or 'skipped'."""
        event_id = meeting.get("eventId")
        if not event_id:
            return "skipped"

        hearing_id = f"{chamber}-{congress}-{event_id}"

        # Fetch meeting detail
        detail_url = meeting.get("url")
        if detail_url:
            detail = self._api_get(detail_url, {"api_key": api_key, "format": "json"})
        else:
            detail = None

        detail_data = detail.get("committeeMeeting", {}) if detail else {}

        # Determine meeting type
        meeting_type_raw = detail_data.get("type", "Meeting").lower()
        if "hearing" in meeting_type_raw:
            meeting_type = "hearing"
        elif "markup" in meeting_type_raw:
            meeting_type = "markup"
        else:
            meeting_type = "meeting"

        # Parse date
        date_str = detail_data.get("date") or meeting.get("date", "")
        meeting_date = _parse_datetime(date_str)

        # Meeting status
        status_raw = detail_data.get("meetingStatus", "Scheduled").lower()
        status_map = {
            "scheduled": "scheduled",
            "canceled": "canceled",
            "postponed": "postponed",
            "rescheduled": "rescheduled",
        }
        meeting_status = status_map.get(status_raw, "scheduled")

        title = detail_data.get("title", "") or meeting.get("title", "Unknown hearing")

        # Location
        room = detail_data.get("room", "")
        building = detail_data.get("building", "")

        # Find committee
        committee = None
        committees_data = detail_data.get("committees", [])
        if committees_data:
            system_code = committees_data[0].get("systemCode", "")
            if system_code:
                try:
                    committee = Committee.objects.get(committee_id=system_code)
                except Committee.DoesNotExist:
                    pass

        # Jacket number (from hearing transcripts if available)
        jacket_number = ""
        hearing_transcripts = detail_data.get("hearingTranscripts", [])
        if hearing_transcripts:
            jacket_number = str(hearing_transcripts[0].get("jacketNumber", ""))

        # Source URL
        source_url = ""
        if detail_url:
            source_url = detail_url.split("?")[0]

        # Transcript URL
        transcript_url = ""
        formats_data = detail_data.get("formats", [])
        for fmt in formats_data:
            if (
                fmt.get("type") == "Formatted Text"
                or "pdf" in fmt.get("type", "").lower()
            ):
                transcript_url = fmt.get("url", "")
                break

        hearing, was_created = Hearing.objects.update_or_create(
            hearing_id=hearing_id,
            defaults={
                "jacket_number": jacket_number,
                "event_id": str(event_id),
                "congress": congress,
                "chamber": chamber,
                "title": title,
                "meeting_type": meeting_type,
                "meeting_status": meeting_status,
                "date": meeting_date,
                "room": room,
                "building": building,
                "committee": committee,
                "transcript_url": transcript_url,
                "source_url": source_url,
            },
        )

        # Process witnesses
        self._process_witnesses(hearing, detail_data)

        # Link related bills
        self._link_related_bills(hearing, detail_data, congress)

        return "created" if was_created else "updated"

    def _process_witnesses(self, hearing: Hearing, detail_data: dict) -> None:
        """Extract and save witness information."""
        witnesses = detail_data.get("witnesses", [])
        if not witnesses:
            return

        # Clear existing witnesses for this hearing (to handle updates)
        HearingWitness.objects.filter(hearing=hearing).delete()

        for witness_data in witnesses:
            name = witness_data.get("name", "")
            if not name:
                continue

            position = witness_data.get("position", "")
            organization = witness_data.get("organization", "")

            # Extract document URLs
            statement_url = ""
            biography_url = ""
            for doc in witness_data.get("documents", []):
                doc_type = doc.get("documentType", "").lower()
                doc_url = doc.get("url", "")
                if "statement" in doc_type:
                    statement_url = doc_url
                elif "biography" in doc_type:
                    biography_url = doc_url

            HearingWitness.objects.create(
                hearing=hearing,
                name=name,
                position=position,
                organization=organization,
                statement_url=statement_url,
                biography_url=biography_url,
            )

    def _link_related_bills(
        self, hearing: Hearing, detail_data: dict, congress: int
    ) -> None:
        """Link hearing to related bills mentioned in the meeting data."""
        related = detail_data.get("bills", [])
        if not related:
            return

        bill_ids = []
        for bill_data in related:
            bill_type = bill_data.get("type", "").lower()
            bill_number = bill_data.get("number")
            bill_congress = bill_data.get("congress", congress)

            if bill_type and bill_number:
                bill_id = f"{bill_type}{bill_number}-{bill_congress}"
                try:
                    bill = Bill.objects.get(bill_id=bill_id)
                    bill_ids.append(bill.bill_id)
                except Bill.DoesNotExist:
                    pass

        if bill_ids:
            hearing.related_bills.set(Bill.objects.filter(bill_id__in=bill_ids))

    def _api_get(self, url: str, params: dict) -> dict | None:
        """Make an API request with retry logic."""
        for attempt in range(3):
            try:
                time.sleep(0.3 if attempt == 0 else 2.0)
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(f"  API request failed after 3 attempts: {e}")
        return None


def _parse_datetime(date_str: str | None) -> datetime | None:
    """Parse ISO datetime string from Congress.gov API."""
    if not date_str:
        return None
    for fmt in [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None
