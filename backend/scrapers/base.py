from abc import ABC, abstractmethod
from typing import Any


class BaseScraper(ABC):
    source: str = ""

    @abstractmethod
    def run(self, client_id: str) -> list[dict[str, Any]]:
        """Fetch public data and return a list of raw company dicts."""

    def _make_company(
        self,
        name: str,
        source_url: str,
        raw: dict[str, Any],
        *,
        sector: str = "Unknown",
        stage: str = "Unknown",
        funding_total: float | None = None,
        latest_round_size: float | None = None,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "sector": sector,
            "stage": stage,
            "funding_total": funding_total,
            "latest_round_size": latest_round_size,
            "source": self.source,
            "source_url": source_url,
            "raw_data": raw,
        }
