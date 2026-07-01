import re
import feedparser

from .base import BaseScraper

_FEEDS = [
    "https://techcrunch.com/tag/funding/feed/",
    "https://venturebeat.com/category/deals/feed/",
]

# Matches titles like "Acme Corp raises $10M Series A" or "FooCo secures $50M"
_FUNDING_RE = re.compile(
    r"^(?P<company>[A-Z][A-Za-z0-9\s&.,'\-]+?)\s+"
    r"(?:raises?|secures?|closes?|lands?|gets?)\s+"
    r"\$(?P<amount>[\d,.]+)\s*(?P<unit>[MBKmbk]?)",
)

_UNIT_MULT = {
    "M": 1_000_000, "m": 1_000_000,
    "B": 1_000_000_000, "b": 1_000_000_000,
    "K": 1_000, "k": 1_000,
}


def _parse_amount(amount_str: str, unit: str) -> float | None:
    try:
        return float(amount_str.replace(",", "")) * _UNIT_MULT.get(unit, 1)
    except ValueError:
        return None


class RssScraper(BaseScraper):
    """Parses funding announcements from TechCrunch and VentureBeat RSS feeds."""

    source = "rss"

    def run(self, client_id: str) -> list[dict]:
        companies = []

        for feed_url in _FEEDS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", feed_url)

                match = _FUNDING_RE.match(title)
                if not match:
                    continue

                name = match.group("company").strip(" ,.")
                amount = _parse_amount(match.group("amount"), match.group("unit"))

                raw = {
                    "title": title,
                    "link": link,
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "feed": feed_url,
                }
                companies.append(
                    self._make_company(
                        name,
                        link,
                        raw,
                        stage="Fundraising",
                        latest_round_size=amount,
                    )
                )

        return companies
