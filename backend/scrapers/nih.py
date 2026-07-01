import httpx
from datetime import datetime, timezone

from .base import BaseScraper

_API_URL = "https://api.reporter.nih.gov/v2/projects/search"


class NihScraper(BaseScraper):
    """Scrapes NIH Reporter for recent SBIR Phase I/II grants (early-stage biotech/health companies)."""

    source = "nih"

    def run(self, client_id: str) -> list[dict]:
        current_year = datetime.now(timezone.utc).year

        payload = {
            "criteria": {
                "fiscal_years": [current_year, current_year - 1],
                "activity_codes": ["R43", "R44"],  # SBIR Phase I and II
            },
            "limit": 50,
            "offset": 0,
            "sort_field": "award_amount",
            "sort_order": "desc",
        }

        with httpx.Client(timeout=30) as http:
            resp = http.post(_API_URL, json=payload)
            resp.raise_for_status()

        companies = []
        seen_names: set[str] = set()

        for project in resp.json().get("results", []):
            org = project.get("organization", {})
            name = (org.get("org_name") or "").strip().title()
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            amount = self._parse_amount(project.get("award_amount"))
            project_num = project.get("project_num", "")
            url = f"https://reporter.nih.gov/project-details/{project_num}"

            raw = {
                "project_num": project_num,
                "title": project.get("project_title", ""),
                "org_name": name,
                "award_amount": amount,
                "fiscal_year": project.get("fiscal_year"),
                "pi_names": project.get("principal_investigators", []),
            }

            companies.append(
                self._make_company(
                    name,
                    url,
                    raw,
                    sector="BioTech",
                    stage="Grant",
                    latest_round_size=amount,
                )
            )

        return companies

    def _parse_amount(self, value) -> float | None:
        try:
            return float(value) if value else None
        except (TypeError, ValueError):
            return None
