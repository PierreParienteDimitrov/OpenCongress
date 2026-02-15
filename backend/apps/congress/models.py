"""
Congressional data models for CongressTrack.
"""

from django.db import models


class Member(models.Model):
    """A member of Congress (Representative or Senator)."""

    class Party(models.TextChoices):
        DEMOCRAT = "D", "Democrat"
        REPUBLICAN = "R", "Republican"
        INDEPENDENT = "I", "Independent"

    class Chamber(models.TextChoices):
        HOUSE = "house", "House of Representatives"
        SENATE = "senate", "Senate"

    # Primary identifier
    bioguide_id = models.CharField(max_length=10, primary_key=True)

    # Basic info
    full_name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, blank=True)

    # Political info
    party = models.CharField(max_length=1, choices=Party.choices)
    chamber = models.CharField(max_length=10, choices=Chamber.choices)
    state = models.CharField(max_length=2)
    district = models.IntegerField(null=True, blank=True)  # Only for House

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    office_address = models.TextField(blank=True)
    website_url = models.URLField(blank=True)
    contact_url = models.URLField(blank=True)

    # Social media
    twitter_handle = models.CharField(max_length=50, blank=True)
    facebook_id = models.CharField(max_length=100, blank=True)
    youtube_id = models.CharField(max_length=100, blank=True)

    # Bio
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, blank=True)

    # Service
    seniority_date = models.DateField(null=True, blank=True)
    term_start = models.DateField(null=True, blank=True)
    term_end = models.DateField(null=True, blank=True)

    # Photos
    photo_url = models.URLField(blank=True)

    # AI-generated content
    ai_bio = models.TextField(blank=True)
    ai_bio_model = models.CharField(max_length=50, blank=True)
    ai_bio_created_at = models.DateTimeField(null=True, blank=True)
    ai_bio_prompt_version = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "members"
        indexes = [
            models.Index(fields=["chamber", "state"]),
            models.Index(fields=["state", "district"]),  # For "Find My Rep" queries
            models.Index(fields=["party"]),
            models.Index(fields=["last_name"]),
            models.Index(fields=["is_active"]),
            models.Index(
                fields=["chamber", "party", "state"],
                name="member_filter_idx",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.party}-{self.state})"


class Seat(models.Model):
    """A physical seat in the chamber for hemicycle visualization."""

    class Section(models.TextChoices):
        DEMOCRAT = "democrat", "Democrat"
        REPUBLICAN = "republican", "Republican"
        INDEPENDENT = "independent", "Independent"

    seat_id = models.CharField(max_length=50, primary_key=True)
    chamber = models.CharField(max_length=10, choices=Member.Chamber.choices)
    section = models.CharField(max_length=20, choices=Section.choices)
    row = models.IntegerField()
    position = models.IntegerField()

    # SVG coordinates for visualization
    svg_x = models.FloatField()
    svg_y = models.FloatField()

    # Current occupant (can be null if vacant)
    member = models.OneToOneField(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seat",
    )

    class Meta:
        db_table = "seats"

    def __str__(self):
        return f"{self.seat_id}"


class Bill(models.Model):
    """A bill or resolution in Congress."""

    class BillType(models.TextChoices):
        HR = "hr", "House Bill"
        S = "s", "Senate Bill"
        HJRES = "hjres", "House Joint Resolution"
        SJRES = "sjres", "Senate Joint Resolution"
        HCONRES = "hconres", "House Concurrent Resolution"
        SCONRES = "sconres", "Senate Concurrent Resolution"
        HRES = "hres", "House Resolution"
        SRES = "sres", "Senate Resolution"

    bill_id = models.CharField(max_length=50, primary_key=True)
    bill_type = models.CharField(max_length=10, choices=BillType.choices)
    number = models.IntegerField()
    congress = models.IntegerField()

    title = models.TextField()
    short_title = models.CharField(max_length=500, blank=True)
    display_number = models.CharField(max_length=50)

    # Content
    summary_text = models.TextField(blank=True)
    summary_html = models.TextField(blank=True)

    # AI-generated summary
    ai_summary = models.TextField(blank=True)
    ai_summary_model = models.CharField(max_length=50, blank=True)
    ai_summary_created_at = models.DateTimeField(null=True, blank=True)
    ai_summary_prompt_version = models.CharField(max_length=20, blank=True)

    # Sponsor
    sponsor = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sponsored_bills",
    )

    # Status
    introduced_date = models.DateField(null=True, blank=True)
    latest_action_date = models.DateField(null=True, blank=True)
    latest_action_text = models.TextField(blank=True)

    # URLs
    congress_url = models.URLField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bills"
        indexes = [
            models.Index(fields=["congress", "bill_type"]),
            models.Index(fields=["introduced_date"]),
        ]

    def __str__(self):
        return f"{self.display_number}: {self.short_title or self.title[:50]}"


class Vote(models.Model):
    """A roll-call vote in Congress."""

    class VoteResult(models.TextChoices):
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"
        AGREED = "agreed", "Agreed to"
        REJECTED = "rejected", "Rejected"

    vote_id = models.CharField(max_length=50, primary_key=True)
    chamber = models.CharField(max_length=10, choices=Member.Chamber.choices)
    congress = models.IntegerField()
    session = models.IntegerField()
    roll_call = models.IntegerField()

    date = models.DateField()
    time = models.TimeField(null=True, blank=True)

    question = models.CharField(max_length=200)
    question_text = models.TextField(blank=True)
    description = models.TextField()
    vote_type = models.CharField(max_length=50, blank=True)
    result = models.CharField(max_length=20, choices=VoteResult.choices)

    # Related bill (if any)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="votes",
    )

    # Vote totals
    total_yea = models.IntegerField(default=0)
    total_nay = models.IntegerField(default=0)
    total_present = models.IntegerField(default=0)
    total_not_voting = models.IntegerField(default=0)

    # Party breakdown - Democrats
    dem_yea = models.IntegerField(default=0)
    dem_nay = models.IntegerField(default=0)
    dem_present = models.IntegerField(default=0)
    dem_not_voting = models.IntegerField(default=0)

    # Party breakdown - Republicans
    rep_yea = models.IntegerField(default=0)
    rep_nay = models.IntegerField(default=0)
    rep_present = models.IntegerField(default=0)
    rep_not_voting = models.IntegerField(default=0)

    # Party breakdown - Independents
    ind_yea = models.IntegerField(default=0)
    ind_nay = models.IntegerField(default=0)
    ind_present = models.IntegerField(default=0)
    ind_not_voting = models.IntegerField(default=0)

    # Bipartisan flag
    is_bipartisan = models.BooleanField(default=False)

    # Source URL
    source_url = models.URLField(blank=True)

    # AI-generated summary
    ai_summary = models.TextField(blank=True)
    ai_summary_model = models.CharField(max_length=50, blank=True)
    ai_summary_created_at = models.DateTimeField(null=True, blank=True)
    ai_summary_prompt_version = models.CharField(max_length=20, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "votes"
        indexes = [
            models.Index(fields=["chamber", "date"]),
            models.Index(fields=["congress", "session"]),
            models.Index(fields=["-date", "-time"]),
            models.Index(fields=["bill"]),
        ]

    def __str__(self):
        return f"{self.vote_id}: {self.description[:50]}"


class MemberVote(models.Model):
    """A member's position on a specific vote."""

    class Position(models.TextChoices):
        YEA = "yea", "Yea"
        NAY = "nay", "Nay"
        PRESENT = "present", "Present"
        NOT_VOTING = "not_voting", "Not Voting"

    id = models.BigAutoField(primary_key=True)
    vote = models.ForeignKey(
        Vote,
        on_delete=models.CASCADE,
        related_name="member_votes",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    position = models.CharField(max_length=15, choices=Position.choices)

    class Meta:
        db_table = "member_votes"
        unique_together = ("vote", "member")
        indexes = [
            models.Index(fields=["member", "position"]),
            models.Index(fields=["vote", "position"]),
        ]

    def __str__(self):
        return f"{self.member.full_name}: {self.position} on {self.vote.vote_id}"


class Committee(models.Model):
    """A congressional committee."""

    class CommitteeType(models.TextChoices):
        STANDING = "standing", "Standing"
        SELECT = "select", "Select"
        JOINT = "joint", "Joint"
        SUBCOMMITTEE = "subcommittee", "Subcommittee"

    class CommitteeChamber(models.TextChoices):
        HOUSE = "house", "House"
        SENATE = "senate", "Senate"
        JOINT = "joint", "Joint"

    committee_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=255)
    chamber = models.CharField(max_length=10, choices=CommitteeChamber.choices)
    committee_type = models.CharField(
        max_length=20, choices=CommitteeType.choices, default=CommitteeType.STANDING
    )
    url = models.URLField(blank=True)

    # Subcommittee relationship
    parent_committee = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subcommittees",
    )

    # AI-generated content
    ai_summary = models.TextField(blank=True)
    ai_summary_model = models.CharField(max_length=50, blank=True)
    ai_summary_created_at = models.DateTimeField(null=True, blank=True)
    ai_summary_prompt_version = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "committees"
        ordering = ["chamber", "name"]

    def __str__(self):
        return f"{self.name} ({self.chamber})"


class CommitteeMember(models.Model):
    """A member's assignment to a committee."""

    class Role(models.TextChoices):
        CHAIR = "chair", "Chair"
        RANKING = "ranking", "Ranking Member"
        MEMBER = "member", "Member"

    id = models.BigAutoField(primary_key=True)
    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        related_name="members",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="committee_assignments",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        db_table = "committee_members"
        unique_together = ("committee", "member")

    def __str__(self):
        return f"{self.member.full_name} - {self.committee.name} ({self.role})"


class BillCommittee(models.Model):
    """A bill's referral to a committee."""

    id = models.BigAutoField(primary_key=True)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="committees",
    )
    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        related_name="referred_bills",
    )
    referred_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "bill_committees"
        unique_together = ("bill", "committee")

    def __str__(self):
        return f"{self.bill.display_number} → {self.committee.name}"


class CandidateFinance(models.Model):
    """Campaign finance data for a member from FEC OpenFEC API."""

    id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="finance_records",
    )
    fec_candidate_id = models.CharField(max_length=20)
    election_cycle = models.IntegerField()

    # Fundraising totals
    total_receipts = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_disbursements = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    cash_on_hand = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_individual_contributions = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    total_pac_contributions = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    total_party_contributions = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    candidate_self_contributions = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # AI-generated summary
    ai_summary = models.TextField(blank=True)
    ai_summary_model = models.CharField(max_length=50, blank=True)
    ai_summary_created_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_finance"
        unique_together = ("member", "election_cycle")
        indexes = [
            models.Index(fields=["election_cycle"]),
            models.Index(fields=["fec_candidate_id"]),
        ]

    def __str__(self):
        return f"{self.member.full_name} ({self.election_cycle}): ${self.total_receipts:,.0f}"


class TopContributor(models.Model):
    """Top contributor (organization) to a candidate from FEC data."""

    id = models.BigAutoField(primary_key=True)
    finance_record = models.ForeignKey(
        CandidateFinance,
        on_delete=models.CASCADE,
        related_name="top_contributors",
    )
    contributor_name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    contributor_type = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "top_contributors"
        ordering = ["-total_amount"]

    def __str__(self):
        return f"{self.contributor_name}: ${self.total_amount:,.0f}"


class IndustryContribution(models.Model):
    """Industry-level contribution aggregation for a candidate."""

    id = models.BigAutoField(primary_key=True)
    finance_record = models.ForeignKey(
        CandidateFinance,
        on_delete=models.CASCADE,
        related_name="industry_contributions",
    )
    industry_name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = "industry_contributions"
        ordering = ["-total_amount"]

    def __str__(self):
        return f"{self.industry_name}: ${self.total_amount:,.0f}"


class Hearing(models.Model):
    """A congressional committee hearing."""

    hearing_id = models.CharField(max_length=50, primary_key=True)
    committee = models.ForeignKey(
        Committee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hearings",
    )
    chamber = models.CharField(max_length=10, choices=Member.Chamber.choices)
    congress = models.IntegerField()
    title = models.TextField()
    date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    hearing_type = models.CharField(max_length=50, blank=True)

    # Related bill (if any)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hearings",
    )

    # URLs
    url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)

    # AI-generated summary
    ai_summary = models.TextField(blank=True)
    ai_summary_model = models.CharField(max_length=50, blank=True)
    ai_summary_created_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hearings"
        indexes = [
            models.Index(fields=["congress", "chamber"]),
            models.Index(fields=["-date"]),
            models.Index(fields=["committee"]),
        ]

    def __str__(self):
        return f"{self.hearing_id}: {self.title[:60]}"


class HearingWitness(models.Model):
    """A witness who testified at a hearing."""

    id = models.BigAutoField(primary_key=True)
    hearing = models.ForeignKey(
        Hearing,
        on_delete=models.CASCADE,
        related_name="witnesses",
    )
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255, blank=True)
    organization = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "hearing_witnesses"

    def __str__(self):
        return f"{self.name} ({self.organization})"


class CBOCostEstimate(models.Model):
    """A CBO cost estimate for a bill or proposed legislation."""

    id = models.BigAutoField(primary_key=True)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cbo_estimates",
    )
    title = models.TextField()
    publish_date = models.DateField()
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)

    # Cost figures (in millions of dollars)
    cost_estimate_millions = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    deficit_impact_millions = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    # AI-generated summary
    ai_summary = models.TextField(blank=True)
    ai_summary_model = models.CharField(max_length=50, blank=True)
    ai_summary_created_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cbo_cost_estimates"
        indexes = [
            models.Index(fields=["-publish_date"]),
        ]

    def __str__(self):
        return f"CBO: {self.title[:60]} ({self.publish_date})"
