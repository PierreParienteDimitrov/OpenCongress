"""
Add campaign finance, hearing, and CBO cost estimate models.

Drops stale tables left behind by a previous version of this migration
that partially applied (created tables but crashed before being recorded
in django_migrations), then creates the current schema.
"""

import django.db.models.deletion
from django.db import migrations, models


def _drop_stale_tables(apps, schema_editor):
    """Drop tables that may have been left behind by a previous failed
    run of this migration.  They contain no data because the migration
    never completed, so it is safe to drop and re-create them."""
    stale_tables = [
        "top_contributors",
        "industry_contributions",
        "hearing_witnesses",
        "cbo_cost_estimates",
        "hearings_related_bills",
        "hearings",
        "candidate_finance",  # old table name (now candidate_finances)
        "candidate_finances",
    ]
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        for table in stale_tables:
            if vendor == "postgresql":
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
            else:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}"')


class Migration(migrations.Migration):

    dependencies = [
        ("congress", "0007_add_committee_joint_chamber"),
    ]

    operations = [
        # Clean up any stale tables from a previous failed migration run
        migrations.RunPython(
            _drop_stale_tables,
            migrations.RunPython.noop,
        ),
        # ── CandidateFinance ─────────────────────────────────────────
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
            },
        ),
        # ── CBOCostEstimate ──────────────────────────────────────────
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
                        help_text="URL to CBO publication page", unique=True
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
        # ── Hearing ──────────────────────────────────────────────────
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
                (
                    "room",
                    models.CharField(blank=True, max_length=100),
                ),
                (
                    "building",
                    models.CharField(blank=True, max_length=200),
                ),
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
        # ── HearingWitness ───────────────────────────────────────────
        migrations.CreateModel(
            name="HearingWitness",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "position",
                    models.CharField(blank=True, max_length=255),
                ),
                (
                    "organization",
                    models.CharField(blank=True, max_length=255),
                ),
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
        # ── IndustryContribution ─────────────────────────────────────
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
        # ── TopContributor ───────────────────────────────────────────
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
        # ── Indexes ──────────────────────────────────────────────────
        migrations.AddIndex(
            model_name="candidatefinance",
            index=models.Index(fields=["cycle"], name="candidate_f_cycle_152bf6_idx"),
        ),
        migrations.AddIndex(
            model_name="candidatefinance",
            index=models.Index(
                fields=["fec_candidate_id"],
                name="candidate_f_fec_can_774a18_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="candidatefinance",
            unique_together={("member", "cycle")},
        ),
        migrations.AddIndex(
            model_name="cbocostestimate",
            index=models.Index(
                fields=["congress"],
                name="cbo_cost_es_congres_6a1205_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="cbocostestimate",
            index=models.Index(
                fields=["-publication_date"],
                name="cbo_cost_es_publica_d6ea11_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="cbocostestimate",
            index=models.Index(
                fields=["bill"],
                name="cbo_cost_es_bill_id_91d3b5_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["congress", "chamber"],
                name="hearings_congres_2a6095_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(fields=["-date"], name="hearings_date_4ce0a7_idx"),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["meeting_type"],
                name="hearings_meeting_eede8f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["committee"],
                name="hearings_committ_aabf5e_idx",
            ),
        ),
    ]
