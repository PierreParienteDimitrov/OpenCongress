"""
Seed CBO cost estimates from the Congressional Budget Office RSS feed.

Parses the CBO RSS/XML feed for a given Congress and creates CBOCostEstimate
records, linking them to Bill records when possible.

Usage:
    python manage.py seed_cbo_estimates --congress=119
"""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests
from django.core.management.base import BaseCommand

from apps.congress.models import Bill, CBOCostEstimate

CBO_RSS_URL = "https://www.cbo.gov/rss/{congress}congress-cost-estimates.xml"
CBO_XML_URL = "https://www.cbo.gov/cost-estimates/xml"


class Command(BaseCommand):
    help = "Seed CBO cost estimates from the CBO RSS feed"

    def add_arguments(self, parser):
        parser.add_argument(
            "--congress",
            type=int,
            default=119,
            help="Congress number (default: 119)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max estimates to process (0 = all)",
        )

    def handle(self, *args, **options):
        congress = options["congress"]
        limit = options["limit"]

        self.stdout.write(f"Fetching CBO cost estimates for Congress {congress}...")

        # Fetch RSS feed
        rss_url = CBO_RSS_URL.format(congress=congress)
        items = self._fetch_rss_items(rss_url)

        if not items:
            self.stderr.write(self.style.ERROR("No items found in CBO RSS feed"))
            return

        if limit:
            items = items[:limit]

        self.stdout.write(f"Processing {len(items)} CBO cost estimates...")

        created = 0
        updated = 0
        skipped = 0

        for i, item in enumerate(items):
            if i > 0 and i % 50 == 0:
                self.stdout.write(f"  Processed {i}/{len(items)} estimates...")

            result = self._process_item(item, congress)
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {created}, updated {updated}, "
                f"skipped {skipped} estimates"
            )
        )

    def _fetch_rss_items(self, rss_url: str) -> list[dict]:
        """Fetch and parse the CBO RSS feed."""
        for attempt in range(3):
            try:
                time.sleep(0.5 if attempt > 0 else 0)
                response = requests.get(rss_url, timeout=30)
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == 2:
                    self.stderr.write(f"Failed to fetch CBO RSS feed: {e}")
                    return []

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            self.stderr.write(f"Failed to parse CBO RSS XML: {e}")
            return []

        items = []
        # RSS feeds have <channel><item> structure
        channel = root.find("channel")
        if channel is None:
            # Try Atom-style or direct items
            item_elements = root.findall(".//item")
        else:
            item_elements = channel.findall("item")

        for item_elem in item_elements:
            title = _elem_text(item_elem, "title") or ""
            link = _elem_text(item_elem, "link") or ""
            description = _elem_text(item_elem, "description") or ""
            pub_date = _elem_text(item_elem, "pubDate") or ""

            if link:
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "description": description,
                        "pub_date": pub_date,
                    }
                )

        return items

    def _process_item(self, item: dict, congress: int) -> str:
        """Process a single CBO RSS item. Returns 'created', 'updated', or 'skipped'."""
        cbo_url = item["link"].strip()
        if not cbo_url:
            return "skipped"

        title = item["title"].strip()
        description = item["description"].strip()
        pub_date = _parse_rfc822_date(item["pub_date"])

        # Try to find a matching bill
        bill = self._match_bill(title, congress)

        estimate, was_created = CBOCostEstimate.objects.update_or_create(
            cbo_url=cbo_url,
            defaults={
                "bill": bill,
                "title": title,
                "description": description,
                "publication_date": pub_date,
                "congress": congress,
            },
        )

        if bill:
            self.stdout.write(
                f"  {'Created' if was_created else 'Updated'}: "
                f"{title[:60]} → {bill.display_number}"
            )

        return "created" if was_created else "updated"

    def _match_bill(self, title: str, congress: int) -> Bill | None:
        """Try to extract a bill number from the CBO title and match it."""
        # CBO titles usually start with bill number, e.g.:
        # "H.R. 1234, Some Bill Title"
        # "S. 567, Another Bill Title"
        patterns = [
            (r"H\.R\.\s*(\d+)", "hr"),
            (r"S\.\s*(\d+)", "s"),
            (r"H\.J\.Res\.\s*(\d+)", "hjres"),
            (r"S\.J\.Res\.\s*(\d+)", "sjres"),
            (r"H\.Con\.Res\.\s*(\d+)", "hconres"),
            (r"S\.Con\.Res\.\s*(\d+)", "sconres"),
            (r"H\.Res\.\s*(\d+)", "hres"),
            (r"S\.Res\.\s*(\d+)", "sres"),
        ]

        for pattern, bill_type in patterns:
            match = re.search(pattern, title)
            if match:
                number = match.group(1)
                bill_id = f"{bill_type}{number}-{congress}"
                try:
                    return Bill.objects.get(bill_id=bill_id)
                except Bill.DoesNotExist:
                    pass

        return None


def _elem_text(parent, tag: str) -> str | None:
    """Safely get text from an XML element."""
    elem = parent.find(tag)
    if elem is not None and elem.text:
        return elem.text.strip()
    return None


def _parse_rfc822_date(date_str: str | None):
    """Parse RFC 822 date from RSS pubDate field."""
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.date()
    except (ValueError, TypeError):
        pass
    # Fallback: try ISO format
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
