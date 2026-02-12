"""Enable the pg_trgm extension for trigram-based fuzzy search."""

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("congress", "0003_widen_committee_id"),
    ]

    operations = [
        TrigramExtension(),
    ]
