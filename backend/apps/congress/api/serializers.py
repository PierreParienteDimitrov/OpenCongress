"""
Serializers for the Congress API.
"""

from rest_framework import serializers

from apps.congress.models import (
    Bill,
    CandidateFinance,
    CBOCostEstimate,
    Committee,
    CommitteeMember,
    Hearing,
    HearingWitness,
    IndustryContribution,
    Member,
    MemberVote,
    Seat,
    TopContributor,
    Vote,
)


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


class RepSponsoredBillSerializer(serializers.ModelSerializer):
    """Lightweight serializer for a member's recently active sponsored bills."""

    class Meta:
        model = Bill
        fields = [
            "bill_id",
            "display_number",
            "short_title",
            "latest_action_date",
            "latest_action_text",
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
    """Serializer for vote summary (used in bill detail and vote detail)."""

    bill_id = serializers.CharField(source="bill.bill_id", allow_null=True)
    bill_display_number = serializers.CharField(
        source="bill.display_number", allow_null=True
    )
    bill_short_title = serializers.CharField(source="bill.short_title", allow_null=True)
    bill_title = serializers.CharField(source="bill.title", allow_null=True)

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
            "ai_summary",
            "bill_id",
            "bill_display_number",
            "bill_short_title",
            "bill_title",
        ]


class BillDetailSerializer(serializers.ModelSerializer):
    """Serializer for bill detail views with votes."""

    sponsor = MemberListSerializer(read_only=True, allow_null=True)
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


# ── Committee serializers ────────────────────────────────────────────


class CommitteeMemberSerializer(serializers.ModelSerializer):
    """Nested member info for a committee's member list."""

    bioguide_id = serializers.CharField(source="member.bioguide_id")
    full_name = serializers.CharField(source="member.full_name")
    party = serializers.CharField(source="member.party")
    state = serializers.CharField(source="member.state")
    district = serializers.IntegerField(source="member.district", allow_null=True)
    photo_url = serializers.URLField(source="member.photo_url")
    role_display = serializers.CharField(source="get_role_display")

    class Meta:
        model = CommitteeMember
        fields = [
            "bioguide_id",
            "full_name",
            "party",
            "state",
            "district",
            "photo_url",
            "role",
            "role_display",
        ]


class CommitteeListSerializer(serializers.ModelSerializer):
    """Serializer for committee list views with aggregated metrics."""

    member_count = serializers.SerializerMethodField()
    subcommittee_count = serializers.SerializerMethodField()
    chair = serializers.SerializerMethodField()
    ranking_member = serializers.SerializerMethodField()
    referred_bills_count = serializers.SerializerMethodField()

    class Meta:
        model = Committee
        fields = [
            "committee_id",
            "name",
            "chamber",
            "committee_type",
            "url",
            "parent_committee_id",
            "member_count",
            "subcommittee_count",
            "chair",
            "ranking_member",
            "referred_bills_count",
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_subcommittee_count(self, obj):
        return obj.subcommittees.count()

    def get_chair(self, obj):
        cm = obj.members.select_related("member").filter(role="chair").first()
        if cm:
            return {
                "bioguide_id": cm.member.bioguide_id,
                "full_name": cm.member.full_name,
                "party": cm.member.party,
            }
        return None

    def get_ranking_member(self, obj):
        cm = obj.members.select_related("member").filter(role="ranking").first()
        if cm:
            return {
                "bioguide_id": cm.member.bioguide_id,
                "full_name": cm.member.full_name,
                "party": cm.member.party,
            }
        return None

    def get_referred_bills_count(self, obj):
        return obj.referred_bills.count()


class CommitteeDetailSerializer(serializers.ModelSerializer):
    """Serializer for committee detail views with members and bills."""

    members = serializers.SerializerMethodField()
    subcommittees = serializers.SerializerMethodField()
    referred_bills = serializers.SerializerMethodField()
    chair = serializers.SerializerMethodField()
    ranking_member = serializers.SerializerMethodField()

    class Meta:
        model = Committee
        fields = [
            "committee_id",
            "name",
            "chamber",
            "committee_type",
            "url",
            "parent_committee_id",
            "ai_summary",
            "members",
            "subcommittees",
            "referred_bills",
            "chair",
            "ranking_member",
        ]

    def get_members(self, obj):
        members_qs = obj.members.select_related("member").order_by(
            "role", "member__last_name"
        )
        return CommitteeMemberSerializer(members_qs, many=True).data

    def get_subcommittees(self, obj):
        subs = obj.subcommittees.all()
        return CommitteeListSerializer(subs, many=True).data

    def get_referred_bills(self, obj):
        bill_committees = obj.referred_bills.select_related(
            "bill", "bill__sponsor"
        ).order_by("-bill__latest_action_date")[:20]
        bills = [bc.bill for bc in bill_committees]
        return BillListSerializer(bills, many=True).data

    def get_chair(self, obj):
        cm = obj.members.select_related("member").filter(role="chair").first()
        if cm:
            return {
                "bioguide_id": cm.member.bioguide_id,
                "full_name": cm.member.full_name,
                "party": cm.member.party,
            }
        return None

    def get_ranking_member(self, obj):
        cm = obj.members.select_related("member").filter(role="ranking").first()
        if cm:
            return {
                "bioguide_id": cm.member.bioguide_id,
                "full_name": cm.member.full_name,
                "party": cm.member.party,
            }
        return None


# ── Campaign Finance serializers ───────────────────────────────────────


class TopContributorSerializer(serializers.ModelSerializer):
    """Serializer for a top contributor to a candidate."""

    class Meta:
        model = TopContributor
        fields = ["contributor_name", "total_amount", "rank"]


class IndustryContributionSerializer(serializers.ModelSerializer):
    """Serializer for an industry contribution to a candidate."""

    class Meta:
        model = IndustryContribution
        fields = ["industry_name", "total_amount", "rank"]


class CandidateFinanceListSerializer(serializers.ModelSerializer):
    """Serializer for candidate finance summary in list views."""

    member_name = serializers.CharField(source="member.full_name")
    member_party = serializers.CharField(source="member.party")
    member_state = serializers.CharField(source="member.state")

    class Meta:
        model = CandidateFinance
        fields = [
            "fec_candidate_id",
            "cycle",
            "member_name",
            "member_party",
            "member_state",
            "total_receipts",
            "total_disbursements",
            "cash_on_hand",
            "individual_contributions",
            "pac_contributions",
        ]


class CandidateFinanceDetailSerializer(serializers.ModelSerializer):
    """Serializer for candidate finance detail with contributors."""

    member_name = serializers.CharField(source="member.full_name")
    member_party = serializers.CharField(source="member.party")
    member_state = serializers.CharField(source="member.state")
    member_chamber = serializers.CharField(source="member.chamber")
    member_photo_url = serializers.URLField(source="member.photo_url")
    top_contributors = TopContributorSerializer(many=True, read_only=True)
    industry_contributions = IndustryContributionSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = CandidateFinance
        fields = [
            "fec_candidate_id",
            "cycle",
            "member_name",
            "member_party",
            "member_state",
            "member_chamber",
            "member_photo_url",
            "total_receipts",
            "total_disbursements",
            "cash_on_hand",
            "debt",
            "individual_contributions",
            "pac_contributions",
            "small_contributions",
            "large_contributions",
            "coverage_start_date",
            "coverage_end_date",
            "top_contributors",
            "industry_contributions",
            "updated_at",
        ]


# ── Hearing serializers ────────────────────────────────────────────────


class HearingWitnessSerializer(serializers.ModelSerializer):
    """Serializer for a witness at a hearing."""

    class Meta:
        model = HearingWitness
        fields = [
            "name",
            "position",
            "organization",
            "statement_url",
            "biography_url",
        ]


class HearingListSerializer(serializers.ModelSerializer):
    """Serializer for hearing list views."""

    committee_name = serializers.CharField(
        source="committee.name", allow_null=True
    )
    committee_id = serializers.CharField(
        source="committee.committee_id", allow_null=True
    )
    witness_count = serializers.SerializerMethodField()
    related_bill_count = serializers.SerializerMethodField()

    class Meta:
        model = Hearing
        fields = [
            "hearing_id",
            "title",
            "chamber",
            "meeting_type",
            "meeting_status",
            "date",
            "room",
            "building",
            "committee_name",
            "committee_id",
            "witness_count",
            "related_bill_count",
        ]

    def get_witness_count(self, obj):
        return obj.witnesses.count()

    def get_related_bill_count(self, obj):
        return obj.related_bills.count()


class HearingDetailSerializer(serializers.ModelSerializer):
    """Serializer for hearing detail views with witnesses and bills."""

    committee_name = serializers.CharField(
        source="committee.name", allow_null=True
    )
    committee_id = serializers.CharField(
        source="committee.committee_id", allow_null=True
    )
    witnesses = HearingWitnessSerializer(many=True, read_only=True)
    related_bills = BillListSerializer(many=True, read_only=True)

    class Meta:
        model = Hearing
        fields = [
            "hearing_id",
            "jacket_number",
            "event_id",
            "congress",
            "chamber",
            "title",
            "meeting_type",
            "meeting_status",
            "date",
            "room",
            "building",
            "committee_name",
            "committee_id",
            "transcript_url",
            "source_url",
            "ai_summary",
            "witnesses",
            "related_bills",
        ]


# ── CBO Cost Estimate serializers ─────────────────────────────────────


class CBOCostEstimateSerializer(serializers.ModelSerializer):
    """Serializer for CBO cost estimates."""

    bill_id = serializers.CharField(source="bill.bill_id", allow_null=True)
    bill_display_number = serializers.CharField(
        source="bill.display_number", allow_null=True
    )
    bill_short_title = serializers.CharField(
        source="bill.short_title", allow_null=True
    )

    class Meta:
        model = CBOCostEstimate
        fields = [
            "id",
            "title",
            "description",
            "cbo_url",
            "publication_date",
            "congress",
            "ten_year_direct_spending",
            "ten_year_revenues",
            "ten_year_deficit",
            "ai_summary",
            "bill_id",
            "bill_display_number",
            "bill_short_title",
        ]
