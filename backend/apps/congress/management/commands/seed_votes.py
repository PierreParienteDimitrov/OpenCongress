"""
Seed votes from Congress.gov API.

Usage:
    python manage.py seed_votes --congress=119 --limit=100
"""

import os
import time
from datetime import datetime
from typing import Any

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Bill, Member, MemberVote, Vote


class Command(BaseCommand):
    help = "Seed votes from Congress.gov API"

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
            default=100,
            help="Number of votes to fetch (default: 100)",
        )
        parser.add_argument(
            "--chamber",
            type=str,
            choices=["house", "senate", "both"],
            default="both",
            help="Chamber to fetch votes from (default: both)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            self.stderr.write(self.style.ERROR("CONGRESS_API_KEY not set in environment"))
            return

        congress = options["congress"]
        limit = options["limit"]
        chamber = options["chamber"]

        chambers = ["house", "senate"] if chamber == "both" else [chamber]

        total_votes = 0
        total_member_votes = 0

        for ch in chambers:
            self.stdout.write(f"Fetching {ch} votes for Congress {congress}...")
            votes_created, member_votes_created = self._fetch_votes(
                api_key, congress, ch, limit // len(chambers)
            )
            total_votes += votes_created
            total_member_votes += member_votes_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {total_votes} votes with {total_member_votes} member votes"
            )
        )

    def _fetch_votes(
        self, api_key: str, congress: int, chamber: str, limit: int
    ) -> tuple[int, int]:
        """Fetch votes for a chamber and return counts."""
        chamber_endpoint = "house-vote" if chamber == "house" else "senate-vote"
        response_key = "houseRollCallVotes" if chamber == "house" else "senateRollCallVotes"

        url = f"{self.CONGRESS_API_BASE}/{chamber_endpoint}/{congress}"
        params = {
            "api_key": api_key,
            "limit": min(limit, 50),
            "format": "json",
        }

        votes_created = 0
        member_votes_created = 0
        offset = 0

        while votes_created < limit:
            params["offset"] = offset
            try:
                response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                self.stderr.write(f"  Failed to fetch votes: {e}")
                break

            votes = data.get(response_key, [])
            if not votes:
                self.stdout.write("  No more votes found")
                break

            for vote_data in votes:
                if votes_created >= limit:
                    break

                v_created, mv_created = self._process_vote(api_key, vote_data, chamber, congress)
                votes_created += v_created
                member_votes_created += mv_created

            self.stdout.write(f"  Processed {votes_created} votes so far...")

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += len(votes)
            time.sleep(0.3)

        return votes_created, member_votes_created

    def _process_vote(
        self, api_key: str, vote_data: dict[str, Any], chamber: str, congress: int
    ) -> tuple[int, int]:
        """Process a single vote and its member positions."""
        session_raw = vote_data.get("sessionNumber")
        roll_call_raw = vote_data.get("rollCallNumber")

        if session_raw is None or roll_call_raw is None:
            return 0, 0

        session: int = int(session_raw)
        roll_call: int = int(roll_call_raw)

        vote_id = f"{chamber}-{congress}-{session}-{roll_call}"

        # Check if vote already exists
        if Vote.objects.filter(vote_id=vote_id).exists():
            return 0, 0

        # Fetch vote details with party totals
        chamber_endpoint = "house-vote" if chamber == "house" else "senate-vote"
        detail_key = "houseRollCallVote" if chamber == "house" else "senateRollCallVote"

        detail_url = f"{self.CONGRESS_API_BASE}/{chamber_endpoint}/{congress}/{session}/{roll_call}"
        params = {"api_key": api_key, "format": "json"}

        try:
            time.sleep(0.3)
            response = requests.get(detail_url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            detail = response.json().get(detail_key, {})
        except Exception as e:
            self.stderr.write(f"  Failed to fetch vote {vote_id}: {e}")
            return 0, 0

        # Parse date from startDate
        date_str = detail.get("startDate", vote_data.get("startDate", ""))
        vote_date = None
        if date_str:
            try:
                vote_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            except ValueError:
                try:
                    vote_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                except ValueError:
                    pass

        if vote_date is None:
            self.stderr.write(f"  Skipping vote {vote_id}: no date found")
            return 0, 0

        # Try to link to a bill
        bill = None
        leg_type = vote_data.get("legislationType", "").lower()
        leg_number = vote_data.get("legislationNumber")
        if leg_type and leg_number:
            bill_id = f"{leg_type}{leg_number}-{congress}"
            try:
                bill = Bill.objects.get(bill_id=bill_id)
            except Bill.DoesNotExist:
                pass

        # Extract party totals
        party_totals = detail.get("votePartyTotal", [])
        dem_totals = {"yea": 0, "nay": 0, "present": 0, "not_voting": 0}
        rep_totals = {"yea": 0, "nay": 0, "present": 0, "not_voting": 0}
        ind_totals = {"yea": 0, "nay": 0, "present": 0, "not_voting": 0}

        for pt in party_totals:
            party_type = pt.get("voteParty", "")
            if party_type == "D":
                dem_totals = {
                    "yea": pt.get("yeaTotal", 0) or 0,
                    "nay": pt.get("nayTotal", 0) or 0,
                    "present": pt.get("presentTotal", 0) or 0,
                    "not_voting": pt.get("notVotingTotal", 0) or 0,
                }
            elif party_type == "R":
                rep_totals = {
                    "yea": pt.get("yeaTotal", 0) or 0,
                    "nay": pt.get("nayTotal", 0) or 0,
                    "present": pt.get("presentTotal", 0) or 0,
                    "not_voting": pt.get("notVotingTotal", 0) or 0,
                }
            elif party_type == "I":
                ind_totals = {
                    "yea": pt.get("yeaTotal", 0) or 0,
                    "nay": pt.get("nayTotal", 0) or 0,
                    "present": pt.get("presentTotal", 0) or 0,
                    "not_voting": pt.get("notVotingTotal", 0) or 0,
                }

        # Calculate totals
        total_yea = dem_totals["yea"] + rep_totals["yea"] + ind_totals["yea"]
        total_nay = dem_totals["nay"] + rep_totals["nay"] + ind_totals["nay"]
        total_present = dem_totals["present"] + rep_totals["present"] + ind_totals["present"]
        total_not_voting = dem_totals["not_voting"] + rep_totals["not_voting"] + ind_totals["not_voting"]

        # Determine if bipartisan
        dem_majority = dem_totals["yea"] > dem_totals["nay"]
        rep_majority = rep_totals["yea"] > rep_totals["nay"]
        is_bipartisan = dem_majority == rep_majority

        # Map result
        result = self._map_result(detail.get("result", vote_data.get("result", "")))

        # Create vote
        vote = Vote.objects.create(
            vote_id=vote_id,
            chamber=chamber,
            congress=congress,
            session=session,
            roll_call=roll_call,
            date=vote_date,
            question=detail.get("voteQuestion", "")[:200],
            question_text=detail.get("voteQuestion", ""),
            description=detail.get("voteQuestion", ""),
            vote_type=detail.get("voteType", ""),
            result=result,
            bill=bill,
            total_yea=total_yea,
            total_nay=total_nay,
            total_present=total_present,
            total_not_voting=total_not_voting,
            dem_yea=dem_totals["yea"],
            dem_nay=dem_totals["nay"],
            dem_present=dem_totals["present"],
            dem_not_voting=dem_totals["not_voting"],
            rep_yea=rep_totals["yea"],
            rep_nay=rep_totals["nay"],
            rep_present=rep_totals["present"],
            rep_not_voting=rep_totals["not_voting"],
            ind_yea=ind_totals["yea"],
            ind_nay=ind_totals["nay"],
            ind_present=ind_totals["present"],
            ind_not_voting=ind_totals["not_voting"],
            is_bipartisan=is_bipartisan,
            source_url=detail.get("sourceDataURL", ""),
        )

        # Fetch and process member votes
        member_votes_created = self._fetch_member_votes(api_key, vote, chamber, congress, session, roll_call)

        return 1, member_votes_created

    def _fetch_member_votes(
        self, api_key: str, vote: Vote, chamber: str, congress: int, session: int, roll_call: int
    ) -> int:
        """Fetch and save individual member votes."""
        chamber_endpoint = "house-vote" if chamber == "house" else "senate-vote"
        response_key = "houseRollCallVoteMemberVotes" if chamber == "house" else "senateRollCallVoteMemberVotes"

        url = f"{self.CONGRESS_API_BASE}/{chamber_endpoint}/{congress}/{session}/{roll_call}/members"
        params = {"api_key": api_key, "format": "json"}

        try:
            time.sleep(0.3)
            response = requests.get(url, params=params, timeout=30)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json().get(response_key, {})
        except Exception as e:
            self.stderr.write(f"    Failed to fetch member votes: {e}")
            return 0

        positions_map = {
            "yea": "yea",
            "aye": "yea",
            "nay": "nay",
            "no": "nay",
            "present": "present",
            "not voting": "not_voting",
        }

        results = data.get("results", [])
        created = 0

        for member_data in results:
            bioguide_id = member_data.get("bioguideID")
            vote_cast = member_data.get("voteCast", "").lower()
            position = positions_map.get(vote_cast, "not_voting")

            if not bioguide_id:
                continue

            try:
                member = Member.objects.get(bioguide_id=bioguide_id)
                MemberVote.objects.create(
                    vote=vote,
                    member=member,
                    position=position,
                )
                created += 1
            except Member.DoesNotExist:
                pass
            except Exception:
                pass

        return created

    def _map_result(self, result: str) -> str:
        """Map result string to choices."""
        result_lower = result.lower()
        if "passed" in result_lower:
            return "passed"
        elif "failed" in result_lower:
            return "failed"
        elif "agreed" in result_lower:
            return "agreed"
        elif "rejected" in result_lower:
            return "rejected"
        return "passed"
