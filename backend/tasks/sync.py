"""
Data synchronization tasks.

Fetches latest votes and members from Congress.gov API and Senate.gov XML.
"""

import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, time as time_type
from typing import Any

import requests
from celery import shared_task
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

CONGRESS_API_BASE = "https://api.congress.gov/v3"
SOCIAL_MEDIA_URL = (
    "https://theunitedstates.io/congress-legislators/legislators-social-media.json"
)
SENATE_VOTE_LIST_URL = "https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{congress}_{session}.xml"
SENATE_VOTE_DETAIL_URL = "https://www.senate.gov/legislative/LIS/roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{roll_call:05d}.xml"

CURRENT_CONGRESS = 119


def _get_api_key() -> str | None:
    return os.environ.get("CONGRESS_API_KEY") or getattr(
        settings, "CONGRESS_API_KEY", None
    )


# ---------------------------------------------------------------------------
# sync_recent_votes — runs hourly on weekdays 9am–9pm
# ---------------------------------------------------------------------------


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def sync_recent_votes(self) -> dict:
    """
    Sync recent votes from both chambers.

    Fetches the latest votes from Congress.gov (House) and Senate.gov (Senate),
    creates any new Vote + MemberVote records.

    Returns:
        Dict with sync statistics
    """

    api_key = _get_api_key()
    if not api_key:
        logger.error("CONGRESS_API_KEY not configured")
        return {"success": False, "error": "CONGRESS_API_KEY not configured"}

    try:
        house_created, house_mv = _sync_house_votes(api_key, CURRENT_CONGRESS)
        senate_created, senate_mv = _sync_senate_votes(CURRENT_CONGRESS)

        total_votes = house_created + senate_created
        total_mv = house_mv + senate_mv

        logger.info(
            f"Vote sync complete: {total_votes} new votes, "
            f"{total_mv} member votes "
            f"(House: {house_created}, Senate: {senate_created})"
        )

        return {
            "success": True,
            "votes_created": total_votes,
            "member_votes_created": total_mv,
            "house_votes": house_created,
            "senate_votes": senate_created,
        }

    except Exception as e:
        logger.error(f"Error syncing votes: {e}")
        raise self.retry(exc=e)


# ---------------------------------------------------------------------------
# sync_members — runs weekly on Sunday at 2am
# ---------------------------------------------------------------------------


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def sync_members(self) -> dict:
    """
    Sync current members from Congress.gov API.

    Updates member info (name, party, state, district, photo, social media).

    Returns:
        Dict with sync statistics
    """
    from apps.congress.models import Member

    api_key = _get_api_key()
    if not api_key:
        logger.error("CONGRESS_API_KEY not configured")
        return {"success": False, "error": "CONGRESS_API_KEY not configured"}

    try:
        members_data = _fetch_all_members(api_key)
        social_media = _fetch_social_media()

        created = 0
        updated = 0

        for member_data in members_data:
            bioguide_id = member_data.get("bioguideId")
            if not bioguide_id:
                continue

            social = social_media.get(bioguide_id, {})

            terms = member_data.get("terms", {}).get("item", [])
            current_term = terms[-1] if terms else {}
            chamber = current_term.get("chamber", "").lower()
            if chamber == "house of representatives":
                chamber = "house"

            district = member_data.get("district")
            if district is None and chamber == "house":
                district = 0

            defaults = {
                "full_name": member_data.get("name", ""),
                "first_name": member_data.get("firstName", ""),
                "last_name": member_data.get("lastName", ""),
                "nickname": member_data.get("nickName", "") or "",
                "party": _map_party(member_data.get("partyName", "")),
                "chamber": chamber if chamber in ["house", "senate"] else "house",
                "state": member_data.get("state", ""),
                "district": district,
                "photo_url": member_data.get("depiction", {}).get("imageUrl", "") or "",
                "twitter_handle": social.get("twitter", ""),
                "facebook_id": social.get("facebook", ""),
                "youtube_id": social.get("youtube_id", ""),
                "is_active": True,
            }

            _, was_created = Member.objects.update_or_create(
                bioguide_id=bioguide_id,
                defaults=defaults,
            )

            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(f"Member sync complete: {created} created, {updated} updated")

        return {
            "success": True,
            "created": created,
            "updated": updated,
            "total": created + updated,
        }

    except Exception as e:
        logger.error(f"Error syncing members: {e}")
        raise self.retry(exc=e)


# ===========================================================================
# House vote helpers
# ===========================================================================


def _sync_house_votes(api_key: str, congress: int) -> tuple[int, int]:
    """Fetch recent House votes from Congress.gov API."""
    from apps.congress.models import Vote

    chamber_endpoint = "house-vote"
    response_key = "houseRollCallVotes"

    url = f"{CONGRESS_API_BASE}/{chamber_endpoint}/{congress}"
    params: dict[str, Any] = {
        "api_key": api_key,
        "limit": 50,
        "format": "json",
        "offset": 0,
    }

    votes_created = 0
    member_votes_created = 0

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch House votes: {e}")
        return 0, 0

    votes = data.get(response_key, [])

    for vote_data in votes:
        session_raw = vote_data.get("sessionNumber")
        roll_call_raw = vote_data.get("rollCallNumber")
        if session_raw is None or roll_call_raw is None:
            continue

        session = int(session_raw)
        roll_call = int(roll_call_raw)
        vote_id = f"house-{congress}-{session}-{roll_call}"

        if Vote.objects.filter(vote_id=vote_id).exists():
            continue

        v, mv = _process_house_vote(
            api_key, vote_data, congress, session, roll_call, vote_id
        )
        votes_created += v
        member_votes_created += mv

    return votes_created, member_votes_created


def _process_house_vote(
    api_key: str,
    vote_data: dict,
    congress: int,
    session: int,
    roll_call: int,
    vote_id: str,
) -> tuple[int, int]:
    """Process a single House vote from the API."""
    from apps.congress.models import Bill, Vote

    detail_url = f"{CONGRESS_API_BASE}/house-vote/{congress}/{session}/{roll_call}"
    params: dict[str, Any] = {"api_key": api_key, "format": "json"}

    try:
        time.sleep(0.3)
        response = requests.get(detail_url, params=params, timeout=30)
        response.raise_for_status()
        detail = response.json().get("houseRollCallVote", {})
    except Exception as e:
        logger.warning(f"Failed to fetch House vote {vote_id}: {e}")
        return 0, 0

    # Parse date
    date_str = detail.get("startDate", vote_data.get("startDate", ""))
    vote_date = _parse_iso_date(date_str)
    if vote_date is None:
        logger.warning(f"Skipping vote {vote_id}: no date")
        return 0, 0

    # Link to bill
    bill = None
    leg_type = vote_data.get("legislationType", "").lower()
    leg_number = vote_data.get("legislationNumber")
    if leg_type and leg_number:
        bill_id = f"{leg_type}{leg_number}-{congress}"
        try:
            bill = Bill.objects.get(bill_id=bill_id)
        except Bill.DoesNotExist:
            pass

    # Party totals
    party_totals = detail.get("votePartyTotal", [])
    dem = {"yea": 0, "nay": 0, "present": 0, "not_voting": 0}
    rep = {"yea": 0, "nay": 0, "present": 0, "not_voting": 0}
    ind = {"yea": 0, "nay": 0, "present": 0, "not_voting": 0}

    for pt in party_totals:
        party_type = pt.get("voteParty", "")
        totals = {
            "yea": pt.get("yeaTotal", 0) or 0,
            "nay": pt.get("nayTotal", 0) or 0,
            "present": pt.get("presentTotal", 0) or 0,
            "not_voting": pt.get("notVotingTotal", 0) or 0,
        }
        if party_type == "D":
            dem = totals
        elif party_type == "R":
            rep = totals
        elif party_type == "I":
            ind = totals

    total_yea = dem["yea"] + rep["yea"] + ind["yea"]
    total_nay = dem["nay"] + rep["nay"] + ind["nay"]
    total_present = dem["present"] + rep["present"] + ind["present"]
    total_not_voting = dem["not_voting"] + rep["not_voting"] + ind["not_voting"]

    dem_majority = dem["yea"] > dem["nay"]
    rep_majority = rep["yea"] > rep["nay"]
    is_bipartisan = dem_majority == rep_majority

    result = _map_result(detail.get("result", vote_data.get("result", "")))

    vote = Vote.objects.create(
        vote_id=vote_id,
        chamber="house",
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
        dem_yea=dem["yea"],
        dem_nay=dem["nay"],
        dem_present=dem["present"],
        dem_not_voting=dem["not_voting"],
        rep_yea=rep["yea"],
        rep_nay=rep["nay"],
        rep_present=rep["present"],
        rep_not_voting=rep["not_voting"],
        ind_yea=ind["yea"],
        ind_nay=ind["nay"],
        ind_present=ind["present"],
        ind_not_voting=ind["not_voting"],
        is_bipartisan=is_bipartisan,
        source_url=detail.get("sourceDataURL", ""),
    )

    # Fetch member votes
    mv_created = _fetch_house_member_votes(api_key, vote, congress, session, roll_call)

    return 1, mv_created


def _fetch_house_member_votes(
    api_key: str,
    vote,
    congress: int,
    session: int,
    roll_call: int,
) -> int:
    """Fetch individual member vote positions for a House vote."""
    from apps.congress.models import Member, MemberVote

    url = f"{CONGRESS_API_BASE}/house-vote/{congress}/{session}/{roll_call}/members"
    params: dict[str, Any] = {"api_key": api_key, "format": "json"}

    positions_map = {
        "yea": "yea",
        "aye": "yea",
        "nay": "nay",
        "no": "nay",
        "present": "present",
        "not voting": "not_voting",
    }

    for attempt in range(3):
        try:
            time.sleep(0.5 if attempt == 0 else 2.0)
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json().get("houseRollCallVoteMemberVotes", {})
            break
        except Exception as e:
            if attempt == 2:
                logger.warning(
                    f"Failed to fetch House member votes for {vote.vote_id} "
                    f"after 3 attempts: {e}"
                )
                return 0
            data = {}

    created = 0
    for member_data in data.get("results", []):
        bioguide_id = member_data.get("bioguideID")
        vote_cast = member_data.get("voteCast", "").lower()
        position = positions_map.get(vote_cast, "not_voting")

        if not bioguide_id:
            continue

        try:
            member = Member.objects.get(bioguide_id=bioguide_id)
            MemberVote.objects.get_or_create(
                vote=vote,
                member=member,
                defaults={"position": position},
            )
            created += 1
        except Member.DoesNotExist:
            pass
        except Exception as e:
            logger.warning(f"Failed to create member vote for {bioguide_id}: {e}")

    return created


# ===========================================================================
# Senate vote helpers (XML from Senate.gov)
# ===========================================================================


def _sync_senate_votes(congress: int) -> tuple[int, int]:
    """Fetch recent Senate votes from Senate.gov XML."""

    # Build senator lookup cache
    member_cache = _build_senator_cache()

    # Try both sessions (session 1 and 2)
    votes_created = 0
    member_votes_created = 0

    for session in [1, 2]:
        url = SENATE_VOTE_LIST_URL.format(congress=congress, session=session)
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except Exception:
            continue

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            continue

        votes_elem = root.find("votes")
        if votes_elem is None:
            continue

        vote_elements = votes_elem.findall("vote")

        for vote_elem in vote_elements:
            v, mv = _process_senate_vote(vote_elem, congress, session, member_cache)
            votes_created += v
            member_votes_created += mv

    return votes_created, member_votes_created


def _build_senator_cache() -> dict:
    """Build a lookup cache for matching senators by last_name + state."""
    from apps.congress.api.constants import STATE_ABBREVS
    from apps.congress.models import Member

    state_abbrevs_lower = {k: v.lower() for k, v in STATE_ABBREVS.items()}
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
        state_abbrev = state_abbrevs_lower.get(state, state)

        key = f"{last_name.lower()}_{state_abbrev}"
        cache[key] = member

        if first_name:
            full_key = f"{first_name.lower()}_{last_name.lower()}_{state_abbrev}"
            cache[full_key] = member

    return cache


def _process_senate_vote(
    vote_elem: ET.Element,
    congress: int,
    session: int,
    member_cache: dict,
) -> tuple[int, int]:
    """Process a single Senate vote from the XML list."""
    from apps.congress.models import Vote

    vote_number_text = _xml_text(vote_elem, "vote_number")
    if not vote_number_text:
        return 0, 0

    try:
        roll_call = int(vote_number_text)
    except ValueError:
        return 0, 0

    vote_id = f"senate-{congress}-{session}-{roll_call}"

    if Vote.objects.filter(vote_id=vote_id).exists():
        return 0, 0

    # Fetch detail XML
    detail_url = SENATE_VOTE_DETAIL_URL.format(
        congress=congress, session=session, roll_call=roll_call
    )

    try:
        time.sleep(0.3)
        response = requests.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch Senate vote {vote_id}: {e}")
        return 0, 0

    try:
        detail_root = ET.fromstring(response.content)
    except ET.ParseError as e:
        logger.warning(f"Failed to parse Senate vote {vote_id} XML: {e}")
        return 0, 0

    vote_date = _parse_senate_date(_xml_text(detail_root, "vote_date"))
    if vote_date is None:
        logger.warning(f"Skipping Senate vote {vote_id}: no date")
        return 0, 0

    vote_time = _parse_senate_time(_xml_text(detail_root, "vote_date"))
    question = _xml_text(detail_root, "question") or ""
    question_text = _xml_text(detail_root, "vote_question_text") or question
    vote_title = _xml_text(detail_root, "vote_title") or ""
    vote_result = _xml_text(detail_root, "vote_result") or ""

    # Totals from <count>
    count_elem = detail_root.find("count")
    total_yea = _xml_int(count_elem, "yeas")
    total_nay = _xml_int(count_elem, "nays")
    total_present = _xml_int(count_elem, "present")
    total_not_voting = _xml_int(count_elem, "absent")

    # Member votes + party totals
    members_elem = detail_root.find("members")
    member_votes_data, party_totals = _parse_senate_member_votes(members_elem)

    result = _map_senate_result(vote_result)
    bill = _find_bill_from_issue(_xml_text(vote_elem, "issue"), congress)

    dem_majority_yea = party_totals["D"]["yea"] > party_totals["D"]["nay"]
    rep_majority_yea = party_totals["R"]["yea"] > party_totals["R"]["nay"]
    is_bipartisan = dem_majority_yea == rep_majority_yea

    description = vote_title if vote_title else question_text

    with transaction.atomic():
        vote = Vote.objects.create(
            vote_id=vote_id,
            chamber="senate",
            congress=congress,
            session=session,
            roll_call=roll_call,
            date=vote_date,
            time=vote_time,
            question=question[:200] if question else "",
            question_text=question_text,
            description=description,
            vote_type="",
            result=result,
            bill=bill,
            total_yea=total_yea,
            total_nay=total_nay,
            total_present=total_present,
            total_not_voting=total_not_voting,
            dem_yea=party_totals["D"]["yea"],
            dem_nay=party_totals["D"]["nay"],
            dem_present=party_totals["D"]["present"],
            dem_not_voting=party_totals["D"]["not_voting"],
            rep_yea=party_totals["R"]["yea"],
            rep_nay=party_totals["R"]["nay"],
            rep_present=party_totals["R"]["present"],
            rep_not_voting=party_totals["R"]["not_voting"],
            ind_yea=party_totals["I"]["yea"],
            ind_nay=party_totals["I"]["nay"],
            ind_present=party_totals["I"]["present"],
            ind_not_voting=party_totals["I"]["not_voting"],
            is_bipartisan=is_bipartisan,
            source_url=detail_url,
        )

        mv_created = _create_senate_member_votes(vote, member_votes_data, member_cache)

    return 1, mv_created


def _parse_senate_member_votes(
    members_elem: ET.Element | None,
) -> tuple[list[dict], dict]:
    """Parse member votes from Senate XML and calculate party totals."""
    party_totals: dict[str, dict[str, int]] = {
        "D": {"yea": 0, "nay": 0, "present": 0, "not_voting": 0},
        "R": {"yea": 0, "nay": 0, "present": 0, "not_voting": 0},
        "I": {"yea": 0, "nay": 0, "present": 0, "not_voting": 0},
    }
    member_votes_data: list[dict[str, str]] = []

    if members_elem is None:
        return member_votes_data, party_totals

    for member_elem in members_elem.findall("member"):
        last_name = _xml_text(member_elem, "last_name") or ""
        first_name = _xml_text(member_elem, "first_name") or ""
        party = _xml_text(member_elem, "party") or ""
        state = _xml_text(member_elem, "state") or ""
        vote_cast = _xml_text(member_elem, "vote_cast") or ""

        position = _map_senate_vote_cast(vote_cast)

        member_votes_data.append(
            {
                "last_name": last_name,
                "first_name": first_name,
                "party": party,
                "state": state,
                "position": position,
            }
        )

        party_key = party if party in party_totals else "I"
        party_totals[party_key][position] += 1

    return member_votes_data, party_totals


def _create_senate_member_votes(
    vote, member_votes_data: list[dict], member_cache: dict
) -> int:
    """Create MemberVote records for a Senate vote."""
    from apps.congress.api.constants import STATE_ABBREVS
    from apps.congress.models import MemberVote

    state_abbrevs_lower = {k: v.lower() for k, v in STATE_ABBREVS.items()}
    created = 0

    for mv_data in member_votes_data:
        state_lower = mv_data["state"].lower()
        state_normalized = state_abbrevs_lower.get(state_lower, state_lower)

        key = f"{mv_data['last_name'].lower()}_{state_normalized}"
        member = member_cache.get(key)

        if member is None:
            full_key = (
                f"{mv_data['first_name'].lower()}_"
                f"{mv_data['last_name'].lower()}_"
                f"{state_normalized}"
            )
            member = member_cache.get(full_key)

        if member is None:
            continue

        try:
            MemberVote.objects.get_or_create(
                vote=vote,
                member=member,
                defaults={"position": mv_data["position"]},
            )
            created += 1
        except Exception as e:
            logger.warning(
                f"Failed to create Senate member vote for "
                f"{mv_data['last_name']}: {e}"
            )

    return created


# ===========================================================================
# Member helpers
# ===========================================================================


def _fetch_all_members(api_key: str) -> list:
    """Fetch all current members with pagination."""
    members: list[dict] = []
    offset = 0

    while True:
        url = f"{CONGRESS_API_BASE}/member"
        params: dict[str, Any] = {
            "api_key": api_key,
            "currentMember": "true",
            "limit": 250,
            "offset": offset,
            "format": "json",
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        batch = data.get("members", [])
        members.extend(batch)

        pagination = data.get("pagination", {})
        if pagination.get("next") is None or len(batch) < 250:
            break

        offset += 250
        time.sleep(0.5)

    return members


def _fetch_social_media() -> dict:
    """Fetch social media data from theunitedstates.io."""
    try:
        response = requests.get(SOCIAL_MEDIA_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

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
        logger.warning(f"Failed to fetch social media: {e}")
        return {}


def _map_party(party_name: str) -> str:
    party_map = {
        "Democratic": "D",
        "Republican": "R",
        "Independent": "I",
        "Libertarian": "I",
    }
    return party_map.get(party_name, "I")


# ===========================================================================
# Shared helpers
# ===========================================================================


def _parse_iso_date(date_str: str) -> date | None:
    """Parse ISO date string from Congress.gov API."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def _parse_senate_date(date_str: str | None) -> date | None:
    """Parse date from Senate XML format (e.g., 'January 9, 2025, 02:54 PM')."""
    if not date_str:
        return None
    for fmt in ["%B %d, %Y, %I:%M %p", "%B %d, %Y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_senate_time(date_str: str | None) -> time_type | None:
    """Parse time from Senate XML format."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%B %d, %Y, %I:%M %p")
        return dt.time()
    except ValueError:
        return None


def _map_result(result: str) -> str:
    """Map House result string to Vote.VoteResult choices."""
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


def _map_senate_result(result: str) -> str:
    """Map Senate result string to Vote.VoteResult choices."""
    result_lower = result.lower()
    if "confirmed" in result_lower or "agreed" in result_lower:
        return "agreed"
    elif "rejected" in result_lower or "not confirmed" in result_lower:
        return "rejected"
    elif "passed" in result_lower:
        return "passed"
    elif "failed" in result_lower or "not sustained" in result_lower:
        return "failed"
    return "agreed"


def _map_senate_vote_cast(vote_cast: str) -> str:
    """Map Senate XML vote_cast to position choices."""
    vote_lower = vote_cast.lower().strip()
    if vote_lower in ("yea", "aye"):
        return "yea"
    elif vote_lower in ("nay", "no"):
        return "nay"
    elif vote_lower == "present":
        return "present"
    return "not_voting"


def _find_bill_from_issue(issue: str | None, congress: int):
    """Try to find a Bill from the Senate vote issue field (e.g., 'S. 123')."""
    from apps.congress.models import Bill

    if not issue:
        return None

    patterns = [
        (r"S\.\s*(\d+)", "s"),
        (r"H\.R\.\s*(\d+)", "hr"),
        (r"S\.J\.Res\.\s*(\d+)", "sjres"),
        (r"H\.J\.Res\.\s*(\d+)", "hjres"),
        (r"S\.Con\.Res\.\s*(\d+)", "sconres"),
        (r"H\.Con\.Res\.\s*(\d+)", "hconres"),
        (r"S\.Res\.\s*(\d+)", "sres"),
        (r"H\.Res\.\s*(\d+)", "hres"),
    ]

    for pattern, bill_type in patterns:
        match = re.search(pattern, issue, re.IGNORECASE)
        if match:
            number = match.group(1)
            bill_id = f"{bill_type}{number}-{congress}"
            try:
                return Bill.objects.get(bill_id=bill_id)
            except Bill.DoesNotExist:
                pass

    return None


def _xml_text(elem: ET.Element | None, tag: str) -> str | None:
    """Safely get text from an XML element."""
    if elem is None:
        return None
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


def _xml_int(elem: ET.Element | None, tag: str) -> int:
    """Safely get integer from an XML element."""
    text = _xml_text(elem, tag)
    if text:
        try:
            return int(text)
        except ValueError:
            pass
    return 0
