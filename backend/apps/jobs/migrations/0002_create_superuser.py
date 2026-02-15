"""
One-time data migration to create the admin superuser on production.

This ensures the superuser exists in the production database where we
can't run interactive management commands.

Set ADMIN_PASSWORD in your environment before running this migration.
"""

import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_superuser(apps, schema_editor):
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        return

    User = apps.get_model("users", "User")
    if not User.objects.filter(username="pierre").exists():
        User.objects.create(
            username="pierre",
            email="pierre.parientedimitrov@gmail.com",
            password=make_password(password),
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )


def remove_superuser(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(username="pierre").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_superuser, remove_superuser),
    ]
