"""
Seed CBO cost estimates from the CBO RSS feed.

Usage:
    python manage.py seed_cbo_estimates
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Bill, CBOCostEstimate

CBO_RSS_URL = "https://www.cbo.gov/publications/cost-estimates/rss.xml"


class Command(BaseCommand):
    help = "Seed CBO cost estimates from the CBO RSS feed"

    def add_arguments(self, parser):
        parser.add_argument(
            "--congress",
            type=int,
            default=119,
            help="Congress number for bill linking (default: 119)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of estimates to process (0 = all from feed)",
        )

    def handle(self, *args, **options):
        congress = options["congress"]
        limit = options["limit"]

        self.stdout.write("Fetching CBO cost estimates RSS feed...")

        try:
            response = requests.get(CBO_RSS_URL, timeout=30)
            response.raise_for_status()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch CBO RSS: {e}"))
            return

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            self.stderr.write(self.style.ERROR(f"Failed to parse RSS XML: {e}"))
            return

        # RSS structure: <rss><channel><item>...</item></channel></rss>
        channel = root.find("channel")
        if channel is None:
            self.stderr.write(self.style.ERROR("No <channel> found in RSS"))
            return

        items = channel.findall("item")
        self.stdout.write(f"Found {len(items)} items in RSS feed")

        if limit:
            items = items[:limit]

        created = 0
        updated = 0

        for item in items:
            was_created = self._process_item(item, congress)
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done! Created {created}, updated {updated}")
        )

    def _process_item(self, item: ET.Element, congress: int) -> bool:
        """Process a single RSS item. Returns True if created."""
        title = self._get_text(item, "title") or ""
        link = self._get_text(item, "link") or ""
        description = self._get_text(item, "description") or ""
        pub_date_str = self._get_text(item, "pubDate") or ""

        if not title or not link:
            return False

        # Parse publication date
        publish_date = None
        if pub_date_str:
            for fmt in [
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S GMT",
                "%Y-%m-%d",
            ]:
                try:
                    publish_date = datetime.strptime(pub_date_str.strip(), fmt).date()
                    break
                except ValueError:
                    continue

        if publish_date is None:
            return False

        # Try to link to a bill
        bill = self._find_bill(title, congress)

        defaults = {
            "title": title,
            "publish_date": publish_date,
            "description": description,
            "bill": bill,
        }

        _, was_created = CBOCostEstimate.objects.update_or_create(
            url=link,
            defaults=defaults,
        )

        return was_created

    def _find_bill(self, title: str, congress: int):
        """Try to find a related bill from the CBO estimate title."""
        # CBO titles often contain patterns like "H.R. 1234" or "S. 567"
        patterns = [
            (r"H\.R\.\s*(\d+)", "hr"),
            (r"S\.\s*(\d+)", "s"),
            (r"H\.J\.Res\.\s*(\d+)", "hjres"),
            (r"S\.J\.Res\.\s*(\d+)", "sjres"),
            (r"H\.Con\.Res\.\s*(\d+)", "hconres"),
            (r"S\.Con\.Res\.\s*(\d+)", "sconres"),
        ]

        for pattern, bill_type in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                number = match.group(1)
                bill_id = f"{bill_type}{number}-{congress}"
                try:
                    return Bill.objects.get(bill_id=bill_id)
                except Bill.DoesNotExist:
                    pass

        return None

    def _get_text(self, elem: ET.Element, tag: str) -> str | None:
        """Safely get text from an XML element."""
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
