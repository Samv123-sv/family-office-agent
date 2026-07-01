import httpx
from datetime import datetime, timedelta, timezone

from config import settings
from .base import BaseScraper

_SEARCH_URL = "https://api.github.com/search/users"


class GitHubScraper(BaseScraper):
    """Scrapes GitHub for recently created organizations (proxy for early-stage tech companies)."""

    source = "github"

    def run(self, client_id: str) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        params = {
            "q": f"type:org created:>{since}",
            "sort": "joined",
            "per_page": 30,
        }

        with httpx.Client(timeout=30, headers=headers) as http:
            resp = http.get(_SEARCH_URL, params=params)
            resp.raise_for_status()

        companies = []
        for org in resp.json().get("items", []):
            login = org.get("login", "")
            name = login.replace("-", " ").replace("_", " ").title()
            if not name:
                continue

            url = org.get("html_url") or f"https://github.com/{login}"
            companies.append(self._make_company(name, url, org))

        return companies
