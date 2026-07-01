import httpx
from datetime import datetime, timedelta, timezone

from .base import BaseScraper

_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
# EDGAR requires a descriptive User-Agent identifying the requester
_HEADERS = {"User-Agent": "FamilyOfficeAgent contact@familyoffice.io"}


class EdgarScraper(BaseScraper):
    """Scrapes SEC EDGAR Form D filings (Reg D fundraising exemptions) from the past 30 days."""

    source = "edgar"

    def run(self, client_id: str) -> list[dict]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)

        params = {
            "q": "",
            "forms": "D",
            "dateRange": "custom",
            "startdt": start.strftime("%Y-%m-%d"),
            "enddt": end.strftime("%Y-%m-%d"),
        }

        with httpx.Client(timeout=30, headers=_HEADERS) as http:
            resp = http.get(_SEARCH_URL, params=params)
            resp.raise_for_status()

        companies = []
        for hit in resp.json().get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            name = src.get("entity_name", "").strip()
            if not name:
                continue

            file_num = src.get("file_num", "")
            url = (
                f"https://www.sec.gov/cgi-bin/browse-edgar"
                f"?action=getcompany&filenum={file_num}&type=D"
            )
            companies.append(self._make_company(name, url, src, stage="Fundraising"))

        return companies
