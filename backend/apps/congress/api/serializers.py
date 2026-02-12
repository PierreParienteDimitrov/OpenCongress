"""
Serializers for the Congress API.
"""

from rest_framework import serializers

from apps.congress.models import Bill, Member, MemberVote, Seat, Vote


class MemberListSerializer(serializers.ModelSerializer):
    """Serializer for member list views."""

    class Meta:
        model = Member
        fields = [
            "bioguide_id",
            "full_name",
            "party",
            "chamber",
            "state",
            "district",
            "photo_url",
        ]


class MemberDetailSerializer(serializers.ModelSerializer):
    """Serializer for member detail views with additional data."""

    recent_votes = serializers.SerializerMethodField()
    sponsored_bills_count = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "bioguide_id",
            "full_name",
            "first_name",
            "last_name",
            "party",
            "chamber",
            "state",
            "district",
            "phone",
            "office_address",
            "website_url",
            "contact_url",
            "twitter_handle",
            "facebook_id",
            "youtube_id",
            "photo_url",
            "ai_bio",
            "term_start",
            "term_end",
            "is_active",
            "recent_votes",
            "sponsored_bills_count",
        ]

    def get_recent_votes(self, obj):
        """Get the member's most recent votes."""
        recent = (
            MemberVote.objects.filter(member=obj)
            .select_related("vote", "vote__bill")
            .order_by("-vote__date", "-vote__time")[:10]
        )
        return MemberRecentVoteSerializer(recent, many=True).data

    def get_sponsored_bills_count(self, obj):
        """Get count of bills sponsored by this member."""
        return obj.sponsored_bills.count()


class MemberRecentVoteSerializer(serializers.ModelSerializer):
    """Serializer for a member's recent vote entries."""

    vote_id = serializers.CharField(source="vote.vote_id")
    date = serializers.DateField(source="vote.date")
    question = serializers.CharField(source="vote.question")
    description = serializers.CharField(source="vote.description")
    result = serializers.CharField(source="vote.result")
    bill_id = serializers.CharField(source="vote.bill.bill_id", allow_null=True)
    bill_display_number = serializers.CharField(
        source="vote.bill.display_number", allow_null=True
    )

    class Meta:
        model = MemberVote
        fields = [
            "vote_id",
            "date",
            "question",
            "description",
            "result",
            "position",
            "bill_id",
            "bill_display_number",
        ]


class BillListSerializer(serializers.ModelSerializer):
    """Serializer for bill list views."""

    sponsor_name = serializers.CharField(source="sponsor.full_name", allow_null=True)
    sponsor_id = serializers.CharField(source="sponsor.bioguide_id", allow_null=True)
    has_vote = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = [
            "bill_id",
            "display_number",
            "bill_type",
            "short_title",
            "title",
            "sponsor_name",
            "sponsor_id",
            "introduced_date",
            "latest_action_date",
            "latest_action_text",
            "has_vote",
        ]

    def get_has_vote(self, obj):
        """Check if this bill has any votes."""
        return obj.votes.exists()


class VoteSummarySerializer(serializers.ModelSerializer):
    """Serializer for vote summary (used in bill detail)."""

    class Meta:
        model = Vote
        fields = [
            "vote_id",
            "chamber",
            "date",
            "time",
            "question",
            "result",
            "total_yea",
            "total_nay",
            "total_present",
            "total_not_voting",
            "dem_yea",
            "dem_nay",
            "rep_yea",
            "rep_nay",
            "ind_yea",
            "ind_nay",
            "is_bipartisan",
        ]


class BillDetailSerializer(serializers.ModelSerializer):
    """Serializer for bill detail views with votes."""

    sponsor = MemberListSerializer(read_only=True)
    votes = VoteSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = [
            "bill_id",
            "display_number",
            "bill_type",
            "number",
            "congress",
            "title",
            "short_title",
            "summary_text",
            "summary_html",
            "ai_summary",
            "sponsor",
            "introduced_date",
            "latest_action_date",
            "latest_action_text",
            "congress_url",
            "votes",
        ]


class VoteCalendarSerializer(serializers.ModelSerializer):
    """Serializer for votes in calendar view."""

    bill_display_number = serializers.CharField(
        source="bill.display_number", allow_null=True
    )
    bill_short_title = serializers.CharField(source="bill.short_title", allow_null=True)

    class Meta:
        model = Vote
        fields = [
            "vote_id",
            "chamber",
            "date",
            "time",
            "question",
            "description",
            "result",
            "total_yea",
            "total_nay",
            "bill",
            "bill_display_number",
            "bill_short_title",
            "is_bipartisan",
        ]


class BillCalendarSerializer(serializers.ModelSerializer):
    """Serializer for bills in calendar view (by action date)."""

    sponsor_name = serializers.CharField(source="sponsor.full_name", allow_null=True)
    sponsor_id = serializers.CharField(source="sponsor.bioguide_id", allow_null=True)

    class Meta:
        model = Bill
        fields = [
            "bill_id",
            "display_number",
            "short_title",
            "sponsor_name",
            "sponsor_id",
            "latest_action_date",
            "latest_action_text",
        ]


class SeatMemberSerializer(serializers.ModelSerializer):
    """Lightweight member data embedded inside a seat."""

    class Meta:
        model = Member
        fields = [
            "bioguide_id",
            "full_name",
            "party",
            "state",
            "district",
            "photo_url",
        ]


class SeatSerializer(serializers.ModelSerializer):
    """Serializer for hemicycle seat data (party-colored default view)."""

    member = SeatMemberSerializer(read_only=True)

    class Meta:
        model = Seat
        fields = [
            "seat_id",
            "chamber",
            "section",
            "row",
            "position",
            "svg_x",
            "svg_y",
            "member",
        ]


class SeatVoteOverlaySerializer(serializers.ModelSerializer):
    """Serializer for hemicycle seat data with vote position overlay."""

    member = SeatMemberSerializer(read_only=True)
    vote_position = serializers.CharField(read_only=True, allow_null=True, default=None)

    class Meta:
        model = Seat
        fields = [
            "seat_id",
            "chamber",
            "section",
            "row",
            "position",
            "svg_x",
            "svg_y",
            "member",
            "vote_position",
        ]
