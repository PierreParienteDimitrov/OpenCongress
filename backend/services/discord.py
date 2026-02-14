"""
Discord webhook integration for alerts and notifications.

Sends rich-embed messages to a Discord channel via webhook.
Gracefully no-ops when DISCORD_WEBHOOK_URL is not configured.
"""

import logging
from datetime import datetime, timezone
from enum import Enum

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert level with display label and Discord embed color."""

    ERROR = ("Error", 0xE74C3C)  # Red
    WARNING = ("Warning", 0xF39C12)  # Orange
    INFO = ("Info", 0x2ECC71)  # Green
    CRITICAL = ("Critical", 0x9B59B6)  # Purple


def send_discord_message(
    title: str,
    description: str,
    level: AlertLevel = AlertLevel.INFO,
    fields: list[dict[str, str | bool]] | None = None,
    webhook_url: str = "",
) -> bool:
    """
    Send a rich-embed message to Discord.

    Args:
        title: Embed title.
        description: Embed description/body.
        level: Alert level (determines color).
        fields: Optional list of {"name": ..., "value": ..., "inline": ...}.
        webhook_url: Override webhook URL (defaults to settings).

    Returns:
        True if sent successfully, False otherwise (including no-op).
    """
    url = webhook_url or getattr(settings, "DISCORD_WEBHOOK_URL", "")
    if not url:
        logger.debug("Discord webhook not configured, skipping alert")
        return False

    label, color = level.value

    embed: dict = {
        "title": f"{label}: {title}"[:256],
        "description": description[:4096],
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "OpenCongress Monitor"},
    }

    if fields:
        embed["fields"] = [
            {
                "name": f["name"][:256],
                "value": f["value"][:1024],
                "inline": f.get("inline", True),
            }
            for f in fields[:25]
        ]

    payload = {"embeds": [embed]}

    try:
        response = httpx.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Failed to send Discord alert: {e}")
        return False
