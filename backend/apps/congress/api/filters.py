"""
Filters for the Congress API.
"""

import django_filters  # type: ignore[import-untyped]

from apps.congress.models import Bill, Member, Vote


class MemberFilter(django_filters.FilterSet):
    """Filter for Member list views."""

    party = django_filters.ChoiceFilter(choices=Member.Party.choices)
    chamber = django_filters.ChoiceFilter(choices=Member.Chamber.choices)
    state = django_filters.CharFilter(lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Member
        fields = ["party", "chamber", "state", "is_active"]


class BillFilter(django_filters.FilterSet):
    """Filter for Bill list views."""

    congress = django_filters.NumberFilter()
    bill_type = django_filters.ChoiceFilter(choices=Bill.BillType.choices)
    sponsor = django_filters.CharFilter(field_name="sponsor__bioguide_id")
    introduced_from = django_filters.DateFilter(
        field_name="introduced_date", lookup_expr="gte"
    )
    introduced_to = django_filters.DateFilter(
        field_name="introduced_date", lookup_expr="lte"
    )
    action_from = django_filters.DateFilter(
        field_name="latest_action_date", lookup_expr="gte"
    )
    action_to = django_filters.DateFilter(
        field_name="latest_action_date", lookup_expr="lte"
    )

    class Meta:
        model = Bill
        fields = [
            "congress",
            "bill_type",
            "sponsor",
            "introduced_from",
            "introduced_to",
            "action_from",
            "action_to",
        ]


class VoteFilter(django_filters.FilterSet):
    """Filter for Vote list views."""

    chamber = django_filters.ChoiceFilter(choices=Member.Chamber.choices)
    congress = django_filters.NumberFilter()
    session = django_filters.NumberFilter()
    result = django_filters.ChoiceFilter(choices=Vote.VoteResult.choices)
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    bill = django_filters.CharFilter(field_name="bill__bill_id")
    is_bipartisan = django_filters.BooleanFilter()

    class Meta:
        model = Vote
        fields = [
            "chamber",
            "congress",
            "session",
            "result",
            "date_from",
            "date_to",
            "bill",
            "is_bipartisan",
        ]
