import httpx

from .base import BaseScraper

_API_URL = "https://api.sbir.gov/public/api/awards"

_AGENCY_SECTOR = {
    "NSF": "Deep Tech",
    "NIH": "BioTech",
    "DOE": "CleanTech",
    "DOD": "Defense Tech",
    "NASA": "SpaceTech",
    "USDA": "AgriTech",
    "EPA": "CleanTech",
    "DHS": "GovTech",
}


class SbirScraper(BaseScraper):
    """Scrapes the SBIR/STTR public awards API for recent government grant recipients."""

    source = "sbir"

    def run(self, client_id: str) -> list[dict]:
        params = {
            "rows": 50,
            "start": 0,
            "sortField": "proposal_award_date",
            "sortDir": "desc",
        }

        with httpx.Client(timeout=30) as http:
            resp = http.get(_API_URL, params=params)
            resp.raise_for_status()

        companies = []
        for award in resp.json().get("data", []):
            name = (award.get("company") or "").strip()
            if not name:
                continue

            amount = self._parse_amount(award.get("award_amount"))
            agency = (award.get("agency") or "").upper()
            phase = (award.get("phase") or "").strip()

            url = (
                award.get("company_url")
                or f"https://www.sbir.gov/sbirsearch/award/all"
                f"?f%5B%5D=im_firm_name%3A{name.replace(' ', '+')}"
            )

            companies.append(
                self._make_company(
                    name,
                    url,
                    award,
                    sector=_AGENCY_SECTOR.get(agency, "GovTech"),
                    stage=f"SBIR {phase}".strip() if phase else "SBIR",
                    latest_round_size=amount,
                )
            )

        return companies

    def _parse_amount(self, value) -> float | None:
        try:
            return float(value) if value else None
        except (TypeError, ValueError):
            return None
