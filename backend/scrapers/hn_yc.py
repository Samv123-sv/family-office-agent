import re
import httpx
from datetime import datetime, timedelta, timezone

from .base import BaseScraper

_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"

# Matches: "Launch HN: CompanyName (YC W24) – description"
_LAUNCH_RE = re.compile(
    r"^Launch HN:\s+(?P<company>[^(–\-]+?)\s*(?:\(YC\s+\w+\))?\s*[–\-]",
    re.IGNORECASE,
)


class HnYcScraper(BaseScraper):
    """Scrapes Hacker News for 'Launch HN' posts, which are YC company launches."""

    source = "hn_yc"

    def run(self, client_id: str) -> list[dict]:
        since = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp())

        params = {
            "query": "Launch HN",
            "tags": "story",
            "numericFilters": f"created_at_i>{since}",
            "hitsPerPage": 50,
        }

        with httpx.Client(timeout=30) as http:
            resp = http.get(_ALGOLIA_URL, params=params)
            resp.raise_for_status()

        companies = []
        for hit in resp.json().get("hits", []):
            title = hit.get("title", "")
            match = _LAUNCH_RE.match(title)
            if not match:
                continue

            name = match.group("company").strip()
            object_id = hit.get("objectID", "")
            hn_url = f"https://news.ycombinator.com/item?id={object_id}"
            product_url = hit.get("url") or hn_url

            raw = {
                "title": title,
                "hn_url": hn_url,
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at", ""),
                "author": hit.get("author", ""),
            }

            companies.append(
                self._make_company(name, product_url, raw, stage="Seed")
            )

        return companies
