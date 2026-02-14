"""
Root conftest for pytest.

Provides shared fixtures used across all test modules.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.congress.models import Bill, Member, MemberVote, Seat, Vote
from apps.content.models import WeeklySummary

User = get_user_model()


# ---------------------------------------------------------------------------
# Auth fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user(db):
    """Create a regular test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def api_client():
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticated DRF test client."""
    api_client.force_authenticate(user=user)
    return api_client


# ---------------------------------------------------------------------------
# Congress data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def member(db):
    """Create a test House member."""
    return Member.objects.create(
        bioguide_id="T000001",
        full_name="Jane Test",
        first_name="Jane",
        last_name="Test",
        party=Member.Party.DEMOCRAT,
        chamber=Member.Chamber.HOUSE,
        state="CA",
        district=1,
        is_active=True,
    )


@pytest.fixture
def senator(db):
    """Create a test Senator."""
    return Member.objects.create(
        bioguide_id="S000001",
        full_name="John Senator",
        first_name="John",
        last_name="Senator",
        party=Member.Party.REPUBLICAN,
        chamber=Member.Chamber.SENATE,
        state="TX",
        is_active=True,
    )


@pytest.fixture
def bill(db, member):
    """Create a test bill with a sponsor."""
    return Bill.objects.create(
        bill_id="hr1-119",
        bill_type=Bill.BillType.HR,
        number=1,
        congress=119,
        title="A Test Bill",
        short_title="Test Bill",
        display_number="H.R.1",
        sponsor=member,
        introduced_date="2025-01-01",
        latest_action_date="2025-06-01",
        latest_action_text="Passed House",
    )


@pytest.fixture
def vote(db, bill):
    """Create a test vote linked to a bill."""
    return Vote.objects.create(
        vote_id="h1-119.2025",
        chamber=Member.Chamber.HOUSE,
        congress=119,
        session=1,
        roll_call=1,
        date="2025-06-01",
        question="On Passage",
        description="On Passage of the Test Bill",
        result=Vote.VoteResult.PASSED,
        bill=bill,
        total_yea=220,
        total_nay=210,
    )


@pytest.fixture
def member_vote(db, vote, member):
    """Create a member's vote record."""
    return MemberVote.objects.create(
        vote=vote,
        member=member,
        position=MemberVote.Position.YEA,
    )


@pytest.fixture
def seat(db, member):
    """Create a test seat."""
    return Seat.objects.create(
        seat_id="house-d-1-1",
        chamber=Member.Chamber.HOUSE,
        section=Seat.Section.DEMOCRAT,
        row=1,
        position=1,
        svg_x=100.0,
        svg_y=200.0,
        member=member,
    )


@pytest.fixture
def weekly_summary(db):
    """Create a test weekly summary."""
    return WeeklySummary.objects.create(
        year=2025,
        week_number=1,
        summary_type=WeeklySummary.SummaryType.RECAP,
        content="This week in Congress...",
        model_used="test-model",
        prompt_version="1.0",
    )
