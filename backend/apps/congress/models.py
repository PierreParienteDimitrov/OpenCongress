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

    committee_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255)
    chamber = models.CharField(max_length=10, choices=Member.Chamber.choices)
    url = models.URLField(blank=True)

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
