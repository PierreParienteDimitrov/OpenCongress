# Generated manually for new data source models

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("congress", "0007_add_committee_joint_chamber"),
    ]

    operations = [
        # ── CandidateFinance ──────────────────────────────────────────
        migrations.CreateModel(
            name="CandidateFinance",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                (
                    "fec_candidate_id",
                    models.CharField(blank=True, max_length=20),
                ),
                ("cycle", models.IntegerField()),
                (
                    "total_receipts",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                (
                    "total_disbursements",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                (
                    "cash_on_hand",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                (
                    "debt",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                (
                    "individual_contributions",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                (
                    "pac_contributions",
                    models.DecimalField(decimal_places=2, default=0, max_digits=14),
                ),
                (
                    "small_contributions",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Contributions $200 and under",
                        max_digits=14,
                    ),
                ),
                (
                    "large_contributions",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Contributions over $200",
                        max_digits=14,
                    ),
                ),
                (
                    "coverage_start_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "coverage_end_date",
                    models.DateField(blank=True, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="finances",
                        to="congress.member",
                    ),
                ),
            ],
            options={
                "db_table": "candidate_finances",
                "unique_together": {("member", "cycle")},
            },
        ),
        migrations.AddIndex(
            model_name="candidatefinance",
            index=models.Index(fields=["cycle"], name="candidate_f_cycle_idx"),
        ),
        migrations.AddIndex(
            model_name="candidatefinance",
            index=models.Index(
                fields=["fec_candidate_id"],
                name="candidate_f_fec_id_idx",
            ),
        ),
        # ── TopContributor ────────────────────────────────────────────
        migrations.CreateModel(
            name="TopContributor",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("contributor_name", models.CharField(max_length=255)),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                ("rank", models.IntegerField(default=0)),
                (
                    "candidate_finance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="top_contributors",
                        to="congress.candidatefinance",
                    ),
                ),
            ],
            options={
                "db_table": "top_contributors",
                "ordering": ["rank"],
            },
        ),
        # ── IndustryContribution ──────────────────────────────────────
        migrations.CreateModel(
            name="IndustryContribution",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("industry_name", models.CharField(max_length=255)),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, max_digits=14),
                ),
                ("rank", models.IntegerField(default=0)),
                (
                    "candidate_finance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="industry_contributions",
                        to="congress.candidatefinance",
                    ),
                ),
            ],
            options={
                "db_table": "industry_contributions",
                "ordering": ["rank"],
            },
        ),
        # ── Hearing ───────────────────────────────────────────────────
        migrations.CreateModel(
            name="Hearing",
            fields=[
                (
                    "hearing_id",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                (
                    "jacket_number",
                    models.CharField(blank=True, max_length=20),
                ),
                (
                    "event_id",
                    models.CharField(
                        blank=True,
                        help_text="Committee meeting eventId",
                        max_length=50,
                    ),
                ),
                ("congress", models.IntegerField()),
                (
                    "chamber",
                    models.CharField(
                        choices=[
                            ("house", "House of Representatives"),
                            ("senate", "Senate"),
                        ],
                        max_length=10,
                    ),
                ),
                ("title", models.TextField()),
                (
                    "meeting_type",
                    models.CharField(
                        choices=[
                            ("hearing", "Hearing"),
                            ("markup", "Markup"),
                            ("meeting", "Meeting"),
                        ],
                        default="hearing",
                        max_length=20,
                    ),
                ),
                (
                    "meeting_status",
                    models.CharField(
                        choices=[
                            ("scheduled", "Scheduled"),
                            ("canceled", "Canceled"),
                            ("postponed", "Postponed"),
                            ("rescheduled", "Rescheduled"),
                        ],
                        default="scheduled",
                        max_length=20,
                    ),
                ),
                ("date", models.DateTimeField(blank=True, null=True)),
                ("room", models.CharField(blank=True, max_length=100)),
                ("building", models.CharField(blank=True, max_length=200)),
                ("transcript_url", models.URLField(blank=True)),
                ("source_url", models.URLField(blank=True)),
                ("ai_summary", models.TextField(blank=True)),
                (
                    "ai_summary_model",
                    models.CharField(blank=True, max_length=50),
                ),
                (
                    "ai_summary_created_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "ai_summary_prompt_version",
                    models.CharField(blank=True, max_length=20),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "committee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hearings",
                        to="congress.committee",
                    ),
                ),
                (
                    "related_bills",
                    models.ManyToManyField(
                        blank=True,
                        related_name="hearings",
                        to="congress.bill",
                    ),
                ),
            ],
            options={
                "db_table": "hearings",
                "ordering": ["-date"],
            },
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["congress", "chamber"],
                name="hearing_congress_chamber_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(fields=["-date"], name="hearing_date_idx"),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["meeting_type"], name="hearing_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["committee"], name="hearing_committee_idx"
            ),
        ),
        # ── HearingWitness ────────────────────────────────────────────
        migrations.CreateModel(
            name="HearingWitness",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("position", models.CharField(blank=True, max_length=255)),
                ("organization", models.CharField(blank=True, max_length=255)),
                ("statement_url", models.URLField(blank=True)),
                ("biography_url", models.URLField(blank=True)),
                (
                    "hearing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="witnesses",
                        to="congress.hearing",
                    ),
                ),
            ],
            options={
                "db_table": "hearing_witnesses",
                "ordering": ["name"],
            },
        ),
        # ── CBOCostEstimate ───────────────────────────────────────────
        migrations.CreateModel(
            name="CBOCostEstimate",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                (
                    "title",
                    models.TextField(
                        help_text="CBO title (usually includes bill number)"
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="CBO description or committee context",
                    ),
                ),
                (
                    "cbo_url",
                    models.URLField(
                        help_text="URL to CBO publication page",
                        unique=True,
                    ),
                ),
                (
                    "publication_date",
                    models.DateField(blank=True, null=True),
                ),
                ("congress", models.IntegerField()),
                (
                    "ten_year_direct_spending",
                    models.DecimalField(
                        blank=True,
                        decimal_places=0,
                        help_text="10-year direct spending impact in millions of dollars",
                        max_digits=16,
                        null=True,
                    ),
                ),
                (
                    "ten_year_revenues",
                    models.DecimalField(
                        blank=True,
                        decimal_places=0,
                        help_text="10-year revenue impact in millions of dollars",
                        max_digits=16,
                        null=True,
                    ),
                ),
                (
                    "ten_year_deficit",
                    models.DecimalField(
                        blank=True,
                        decimal_places=0,
                        help_text="10-year deficit impact in millions of dollars",
                        max_digits=16,
                        null=True,
                    ),
                ),
                ("ai_summary", models.TextField(blank=True)),
                (
                    "ai_summary_model",
                    models.CharField(blank=True, max_length=50),
                ),
                (
                    "ai_summary_created_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "ai_summary_prompt_version",
                    models.CharField(blank=True, max_length=20),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "bill",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cbo_estimates",
                        to="congress.bill",
                    ),
                ),
            ],
            options={
                "db_table": "cbo_cost_estimates",
                "ordering": ["-publication_date"],
            },
        ),
        migrations.AddIndex(
            model_name="cbocostestimate",
            index=models.Index(
                fields=["congress"], name="cbo_congress_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="cbocostestimate",
            index=models.Index(
                fields=["-publication_date"], name="cbo_pub_date_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="cbocostestimate",
            index=models.Index(fields=["bill"], name="cbo_bill_idx"),
        ),
    ]
