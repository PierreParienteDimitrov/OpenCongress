"""
Add campaign finance, hearing, and CBO cost estimate models.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("congress", "0007_add_committee_joint_chamber"),
    ]

    operations = [
        # ── CandidateFinance ─────────────────────────────────────────
        migrations.CreateModel(
            name="CandidateFinance",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("fec_candidate_id", models.CharField(max_length=20)),
                ("election_cycle", models.IntegerField()),
                (
                    "total_receipts",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                (
                    "total_disbursements",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                (
                    "cash_on_hand",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                (
                    "total_individual_contributions",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                (
                    "total_pac_contributions",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                (
                    "total_party_contributions",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                (
                    "candidate_self_contributions",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                ("ai_summary", models.TextField(blank=True)),
                ("ai_summary_model", models.CharField(blank=True, max_length=50)),
                (
                    "ai_summary_created_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="finance_records",
                        to="congress.member",
                    ),
                ),
            ],
            options={
                "db_table": "candidate_finance",
                "unique_together": {("member", "election_cycle")},
            },
        ),
        migrations.AddIndex(
            model_name="candidatefinance",
            index=models.Index(
                fields=["election_cycle"],
                name="candidate_f_electio_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="candidatefinance",
            index=models.Index(
                fields=["fec_candidate_id"],
                name="candidate_f_fec_can_idx",
            ),
        ),
        # ── TopContributor ───────────────────────────────────────────
        migrations.CreateModel(
            name="TopContributor",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("contributor_name", models.CharField(max_length=255)),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                ("contributor_type", models.CharField(blank=True, max_length=50)),
                (
                    "finance_record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="top_contributors",
                        to="congress.candidatefinance",
                    ),
                ),
            ],
            options={
                "db_table": "top_contributors",
                "ordering": ["-total_amount"],
            },
        ),
        # ── IndustryContribution ─────────────────────────────────────
        migrations.CreateModel(
            name="IndustryContribution",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("industry_name", models.CharField(max_length=255)),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                (
                    "finance_record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="industry_contributions",
                        to="congress.candidatefinance",
                    ),
                ),
            ],
            options={
                "db_table": "industry_contributions",
                "ordering": ["-total_amount"],
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
                    "chamber",
                    models.CharField(
                        choices=[
                            ("house", "House of Representatives"),
                            ("senate", "Senate"),
                        ],
                        max_length=10,
                    ),
                ),
                ("congress", models.IntegerField()),
                ("title", models.TextField()),
                ("date", models.DateTimeField(blank=True, null=True)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("hearing_type", models.CharField(blank=True, max_length=50)),
                ("url", models.URLField(blank=True)),
                ("video_url", models.URLField(blank=True)),
                ("ai_summary", models.TextField(blank=True)),
                ("ai_summary_model", models.CharField(blank=True, max_length=50)),
                (
                    "ai_summary_created_at",
                    models.DateTimeField(blank=True, null=True),
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
                    "bill",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hearings",
                        to="congress.bill",
                    ),
                ),
            ],
            options={
                "db_table": "hearings",
            },
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["congress", "chamber"],
                name="hearings_congres_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["-date"],
                name="hearings_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hearing",
            index=models.Index(
                fields=["committee"],
                name="hearings_committ_idx",
            ),
        ),
        # ── HearingWitness ───────────────────────────────────────────
        migrations.CreateModel(
            name="HearingWitness",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("position", models.CharField(blank=True, max_length=255)),
                ("organization", models.CharField(blank=True, max_length=255)),
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
            },
        ),
        # ── CBOCostEstimate ──────────────────────────────────────────
        migrations.CreateModel(
            name="CBOCostEstimate",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("title", models.TextField()),
                ("publish_date", models.DateField()),
                ("url", models.URLField(unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "cost_estimate_millions",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=15,
                        null=True,
                    ),
                ),
                (
                    "deficit_impact_millions",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=15,
                        null=True,
                    ),
                ),
                ("ai_summary", models.TextField(blank=True)),
                ("ai_summary_model", models.CharField(blank=True, max_length=50)),
                (
                    "ai_summary_created_at",
                    models.DateTimeField(blank=True, null=True),
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
            },
        ),
        migrations.AddIndex(
            model_name="cbocostestimate",
            index=models.Index(
                fields=["-publish_date"],
                name="cbo_cost_es_publish_idx",
            ),
        ),
    ]
