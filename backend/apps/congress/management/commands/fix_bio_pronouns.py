"""
Fix they/them pronouns in existing AI-generated member bios.

Fetches gender data from unitedstates.io (if not already in the DB),
then uses a lightweight AI call to replace they/them/their with the
correct gendered pronouns without regenerating the entire bio.

Usage:
    python manage.py fix_bio_pronouns              # fix all bios
    python manage.py fix_bio_pronouns --dry-run    # preview changes only
    python manage.py fix_bio_pronouns --member A000123  # fix a single member
"""

import time

import requests
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.congress.models import Member

LEGISLATORS_URL = (
    "https://raw.githubusercontent.com/unitedstates/"
    "congress-legislators/gh-pages/legislators-current.json"
)

PRONOUN_FIX_PROMPT = """You are a copy editor. The following biography uses "they/them/their" pronouns to refer to {full_name}. Rewrite it using {pronoun_subject}/{pronoun_object}/{possessive}/{possessive_pronoun}/{reflexive} pronouns instead.

Rules:
- Only change pronouns that refer to {full_name}. Keep collective pronouns (referring to Congress, committees, or groups) unchanged.
- Adjust verb conjugation accordingly (e.g. "they serve" → "{pronoun_subject} serves", "they have" → "{pronoun_subject} has").
- Do not add, remove, or rephrase any other content. Keep the text identical except for pronoun and verb fixes.
- Return ONLY the corrected text, nothing else.

Biography:
{bio}"""


class Command(BaseCommand):
    help = "Fix they/them pronouns in AI-generated member bios"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving to the database",
        )
        parser.add_argument(
            "--member",
            type=str,
            help="Fix a single member by bioguide_id",
        )

    def handle(self, *args, **options):
        from services import AIService, CacheService

        dry_run = options["dry_run"]
        single_member = options.get("member")

        # --- Step 1: Backfill gender from unitedstates.io ---
        self._backfill_gender(dry_run)

        # --- Step 2: Fix pronouns in bios ---
        ai_service = AIService()

        qs = Member.objects.filter(
            gender__in=["M", "F"],
        ).exclude(ai_bio="")

        qs = qs.filter(
            Q(ai_bio__icontains="they")
            | Q(ai_bio__icontains="their")
            | Q(ai_bio__icontains="them")
        )

        if single_member:
            qs = qs.filter(bioguide_id=single_member)

        members = list(
            qs.values_list("bioguide_id", "full_name", "gender", "ai_bio", "chamber")
        )

        if not members:
            self.stdout.write(self.style.SUCCESS("No bios need pronoun fixing."))
            return

        self.stdout.write(f"\nFound {len(members)} bio(s) to fix pronouns.\n")

        gender_map = {
            "M": ("He", "him", "his", "his", "himself"),
            "F": ("She", "her", "her", "hers", "herself"),
        }

        changed = 0
        unchanged = 0
        errors = 0

        for bioguide_id, full_name, gender, bio, chamber in members:
            (
                pronoun_subject,
                pronoun_object,
                possessive,
                possessive_pronoun,
                reflexive,
            ) = gender_map[gender]

            prompt = PRONOUN_FIX_PROMPT.format(
                full_name=full_name,
                pronoun_subject=pronoun_subject,
                pronoun_object=pronoun_object,
                possessive=possessive,
                possessive_pronoun=possessive_pronoun,
                reflexive=reflexive,
                bio=bio,
            )

            try:
                fixed_bio, tokens = ai_service.generate_completion(
                    prompt, max_tokens=400
                )
                fixed_bio = fixed_bio.strip()
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"  ERROR {full_name} ({bioguide_id}): {e}")
                )
                errors += 1
                continue

            if fixed_bio == bio.strip():
                unchanged += 1
                continue

            changed += 1
            self.stdout.write(f"\n{'=' * 60}")
            self.stdout.write(self.style.WARNING(f"  {full_name} ({bioguide_id})"))
            self.stdout.write(f"  BEFORE: {bio.strip()[:200]}...")
            self.stdout.write(f"  AFTER:  {fixed_bio[:200]}...")

            if not dry_run:
                Member.objects.filter(bioguide_id=bioguide_id).update(ai_bio=fixed_bio)
                CacheService.invalidate_member(bioguide_id, chamber, full_name)

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        self.stdout.write(f"\n{'=' * 60}")
        mode = "DRY RUN" if dry_run else "COMPLETE"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: {changed} changed, {unchanged} unchanged, {errors} errors "
                f"(out of {len(members)} processed)"
            )
        )

    def _backfill_gender(self, dry_run: bool):
        """Fetch gender data from unitedstates.io and backfill the gender field."""
        missing_count = Member.objects.filter(gender="").count()
        if missing_count == 0:
            self.stdout.write("All members already have gender data.")
            return

        self.stdout.write(
            f"Backfilling gender for {missing_count} members from unitedstates.io..."
        )

        try:
            response = requests.get(LEGISLATORS_URL, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch gender data: {e}"))
            return

        # Build bioguide → gender map
        gender_map = {}
        for entry in data:
            bioguide = entry.get("id", {}).get("bioguide")
            gender = entry.get("bio", {}).get("gender")
            if bioguide and gender:
                gender_map[bioguide] = gender

        self.stdout.write(f"  Found gender data for {len(gender_map)} legislators.")

        updated = 0
        for member in Member.objects.filter(gender=""):
            gender = gender_map.get(member.bioguide_id)
            if gender:
                if not dry_run:
                    Member.objects.filter(bioguide_id=member.bioguide_id).update(
                        gender=gender
                    )
                updated += 1

        mode = "Would update" if dry_run else "Updated"
        self.stdout.write(self.style.SUCCESS(f"  {mode} gender for {updated} members."))
