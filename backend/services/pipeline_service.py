import logging
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models.company import Company
from models.pipeline_run import PipelineRun
from scrapers import (
    EdgarScraper,
    GitHubScraper,
    HnYcScraper,
    NihScraper,
    RssScraper,
    SbirScraper,
)

logger = logging.getLogger(__name__)

_DEFAULT_SCRAPERS = [
    EdgarScraper,
    SbirScraper,
    GitHubScraper,
    RssScraper,
    NihScraper,
    HnYcScraper,
]


class PipelineService:
    def __init__(
        self,
        db: Session,
        scrapers=None,
        dispatch_scoring: Callable[[str, str], None] | None = None,
    ):
        self.db = db
        self.scrapers = scrapers if scrapers is not None else [cls() for cls in _DEFAULT_SCRAPERS]
        # Injected for testability; defaults to the real Celery task (lazy import)
        self._dispatch_scoring = dispatch_scoring or self._default_dispatch

    def run_full_pipeline(self, client_id: UUID) -> dict:
        run = self._start_run(client_id)
        all_raw: list[dict] = []
        errors: list[str] = []

        try:
            for scraper in self.scrapers:
                try:
                    results = scraper.run(str(client_id))
                    logger.info("scraper=%s client=%s found=%d", scraper.source, client_id, len(results))
                    all_raw.extend(results)
                except Exception as exc:
                    msg = f"{scraper.source}: {exc}"
                    logger.warning("scraper failed: %s", msg)
                    errors.append(msg)

            unique = self._deduplicate(all_raw)
            new_companies = self._upsert_companies(client_id, unique)
            self._finish_run(run, len(new_companies), errors)  # commits here

            # Dispatch scoring only after commit so rows are visible to the worker
            for company in new_companies:
                self._dispatch_scoring(str(company.id), str(client_id))

        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

        return {
            "pipeline_run_id": str(run.id),
            "total_scraped": len(all_raw),
            "after_dedup": len(unique),
            "new_companies": len(new_companies),
            "scraper_errors": errors,
        }

    # ── private ───────────────────────────────────────────────────────────────

    def _start_run(self, client_id: UUID) -> PipelineRun:
        run = PipelineRun(
            client_id=client_id,
            source="full_pipeline",
            status="running",
            companies_found=0,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.flush()
        return run

    def _deduplicate(self, companies: list[dict]) -> list[dict]:
        seen: set[tuple[str, str]] = set()
        unique = []
        for c in companies:
            key = (c["name"].lower().strip(), c["source"])
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _upsert_companies(self, client_id: UUID, companies: list[dict]) -> list[Company]:
        new_companies: list[Company] = []
        for data in companies:
            exists = (
                self.db.query(Company)
                .filter(
                    and_(
                        Company.client_id == client_id,
                        Company.name == data["name"],
                        Company.source == data["source"],
                    )
                )
                .first()
            )
            if exists:
                continue
            company = Company(client_id=client_id, **data)
            self.db.add(company)
            new_companies.append(company)
        self.db.flush()
        return new_companies

    def _finish_run(self, run: PipelineRun, new_count: int, errors: list[str]) -> None:
        run.status = "completed"
        run.companies_found = new_count
        run.completed_at = datetime.now(timezone.utc)
        if errors:
            run.error_message = "; ".join(errors)
        self.db.commit()

    @staticmethod
    def _default_dispatch(company_id: str, client_id: str) -> None:
        from tasks.scoring_tasks import score_company as score_company_task
        score_company_task.delay(company_id, client_id)
