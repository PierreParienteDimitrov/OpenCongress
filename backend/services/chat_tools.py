"""
Chat tool definitions and execution functions for LLM tool-use.

Defines tools that allow the LLM to query the OpenCongress database
for bills, votes, and members. Each provider (Anthropic, OpenAI, Google)
uses a slightly different tool format — converter functions handle this.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_SEARCH_RESULTS = 10

# ---------------------------------------------------------------------------
# Canonical tool definitions (provider-agnostic, JSON Schema parameters)
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_bill_details",
        "description": (
            "Get full details about a congressional bill including its title, "
            "sponsor, summary, status, and related votes. Use when the user "
            "asks about a specific bill."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "bill_id": {
                    "type": "string",
                    "description": "The bill ID, e.g. 'hr1-119' or 's100-119'",
                }
            },
            "required": ["bill_id"],
        },
    },
    {
        "name": "get_member_details",
        "description": (
            "Get a Congress member's profile including party, state, contact "
            "info, bio, and recent voting record. Use when the user asks "
            "about a specific member of Congress."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The member's Bioguide ID, e.g. 'P000197'",
                }
            },
            "required": ["bioguide_id"],
        },
    },
    {
        "name": "get_vote_details",
        "description": (
            "Get full details about a roll-call vote including totals, party "
            "breakdown, and the related bill. Use when the user asks about "
            "a specific vote."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "vote_id": {
                    "type": "string",
                    "description": "The vote ID, e.g. 'h1-20240115'",
                }
            },
            "required": ["vote_id"],
        },
    },
    {
        "name": "get_member_vote_position",
        "description": (
            "Check how a specific member voted on a specific roll-call vote. "
            "Returns the member's position (yea, nay, present, or not voting)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The member's Bioguide ID",
                },
                "vote_id": {
                    "type": "string",
                    "description": "The vote ID",
                },
            },
            "required": ["bioguide_id", "vote_id"],
        },
    },
    {
        "name": "get_vote_members",
        "description": (
            "Get the list of members who voted a specific way on a vote. "
            "Useful for questions like 'who voted against this bill?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "vote_id": {
                    "type": "string",
                    "description": "The vote ID",
                },
                "position": {
                    "type": "string",
                    "enum": ["yea", "nay", "present", "not_voting"],
                    "description": "Filter by vote position",
                },
            },
            "required": ["vote_id"],
        },
    },
    {
        "name": "search_bills",
        "description": (
            "Search for bills by keyword in their title or display number. "
            "Use when the user asks about a bill but doesn't specify an exact ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords, e.g. 'infrastructure' or 'H.R. 1'",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_members",
        "description": (
            "Search for Congress members by name. Returns a list of matching "
            "members with their party, state, and chamber."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'Pelosi' or 'Cruz'",
                }
            },
            "required": ["query"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution functions
# ---------------------------------------------------------------------------


def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call to the appropriate handler."""
    from collections.abc import Callable

    handlers: dict[str, Callable[..., dict[str, Any]]] = {
        "get_bill_details": _get_bill_details,
        "get_member_details": _get_member_details,
        "get_vote_details": _get_vote_details,
        "get_member_vote_position": _get_member_vote_position,
        "get_vote_members": _get_vote_members,
        "search_bills": _search_bills,
        "search_members": _search_members,
    }
    handler = handlers.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(**args)
    except Exception as e:
        logger.error("Tool execution error (%s): %s", name, e)
        return {"error": f"Tool execution failed: {str(e)}"}


def _get_bill_details(bill_id: str) -> dict[str, Any]:
    from apps.congress.api.serializers import BillDetailSerializer
    from apps.congress.models import Bill

    try:
        bill = (
            Bill.objects.select_related("sponsor")
            .prefetch_related("votes")
            .get(pk=bill_id)
        )
    except Bill.DoesNotExist:
        return {"error": f"Bill '{bill_id}' not found"}
    return BillDetailSerializer(bill).data


def _get_member_details(bioguide_id: str) -> dict[str, Any]:
    from apps.congress.api.serializers import MemberDetailSerializer
    from apps.congress.models import Member

    try:
        member = Member.objects.get(pk=bioguide_id)
    except Member.DoesNotExist:
        return {"error": f"Member '{bioguide_id}' not found"}
    return MemberDetailSerializer(member).data


def _get_vote_details(vote_id: str) -> dict[str, Any]:
    from apps.congress.api.serializers import VoteSummarySerializer
    from apps.congress.models import Vote

    try:
        vote = Vote.objects.select_related("bill").get(pk=vote_id)
    except Vote.DoesNotExist:
        return {"error": f"Vote '{vote_id}' not found"}
    data = VoteSummarySerializer(vote).data
    if vote.bill:
        data["bill_display_number"] = vote.bill.display_number
        data["bill_title"] = vote.bill.short_title or vote.bill.title
    data["description"] = vote.description
    return data


def _get_member_vote_position(bioguide_id: str, vote_id: str) -> dict[str, Any]:
    from apps.congress.models import MemberVote

    try:
        mv = MemberVote.objects.select_related("member", "vote").get(
            member_id=bioguide_id, vote_id=vote_id
        )
    except MemberVote.DoesNotExist:
        return {
            "error": (
                f"No vote record found for member '{bioguide_id}' "
                f"on vote '{vote_id}'"
            )
        }
    return {
        "member_name": mv.member.full_name,
        "member_party": mv.member.party,
        "member_state": mv.member.state,
        "vote_id": vote_id,
        "position": mv.position,
        "vote_question": mv.vote.question,
        "vote_result": mv.vote.result,
    }


def _get_vote_members(vote_id: str, position: str | None = None) -> dict[str, Any]:
    from apps.congress.models import MemberVote

    qs = MemberVote.objects.filter(vote_id=vote_id).select_related("member")
    if position:
        qs = qs.filter(position=position)
    members = [
        {
            "bioguide_id": mv.member.bioguide_id,
            "full_name": mv.member.full_name,
            "party": mv.member.party,
            "state": mv.member.state,
            "position": mv.position,
        }
        for mv in qs[:100]
    ]
    return {
        "vote_id": vote_id,
        "filter_position": position,
        "count": len(members),
        "members": members,
    }


def _search_bills(query: str) -> dict[str, Any]:
    from django.db.models import Q

    from apps.congress.api.serializers import BillListSerializer
    from apps.congress.models import Bill

    qs = (
        Bill.objects.select_related("sponsor")
        .filter(
            Q(title__icontains=query)
            | Q(short_title__icontains=query)
            | Q(display_number__icontains=query)
        )
        .order_by("-latest_action_date")[:MAX_SEARCH_RESULTS]
    )
    results = list(qs)
    return {
        "query": query,
        "count": len(results),
        "bills": BillListSerializer(results, many=True).data,
    }


def _search_members(query: str) -> dict[str, Any]:
    from django.db.models import Q

    from apps.congress.api.serializers import MemberListSerializer
    from apps.congress.models import Member

    qs = (
        Member.objects.filter(is_active=True)
        .filter(Q(full_name__icontains=query))
        .order_by("full_name")[:MAX_SEARCH_RESULTS]
    )
    results = list(qs)
    return {
        "query": query,
        "count": len(results),
        "members": MemberListSerializer(results, many=True).data,
    }


# ---------------------------------------------------------------------------
# Provider-specific tool format converters
# ---------------------------------------------------------------------------


def tools_for_anthropic() -> list[dict[str, Any]]:
    """Convert canonical tools to Anthropic format."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in TOOLS
    ]


def tools_for_openai() -> list[dict[str, Any]]:
    """Convert canonical tools to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in TOOLS
    ]


def tools_for_google() -> list:
    """Convert canonical tools to Google GenAI format."""
    from google.genai import types

    function_declarations = [
        types.FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=t["parameters"],
        )
        for t in TOOLS
    ]
    return [types.Tool(function_declarations=function_declarations)]
