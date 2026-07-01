import uuid
from unittest.mock import MagicMock

import pytest

from models.client import Client
from models.company import Company
from models.pipeline_run import PipelineRun
from services.pipeline_service import PipelineService


# ── helpers ───────────────────────────────────────────────────────────────────

def _company(name: str, source: str, amount: float | None = None) -> dict:
    return {
        "name": name,
        "sector": "FinTech",
        "stage": "Seed",
        "funding_total": None,
        "latest_round_size": amount,
        "source": source,
        "source_url": f"https://example.com/{name.lower().replace(' ', '-')}",
        "raw_data": {},
    }


def _mock_scraper(source: str, companies: list[dict]) -> MagicMock:
    scraper = MagicMock()
    scraper.source = source
    scraper.run.return_value = companies
    return scraper


@pytest.fixture
def client_id(db):
    client = Client(name="Test Family Office", thesis_json={}, config_json={})
    db.add(client)
    db.flush()
    return client.id


# ── tests ─────────────────────────────────────────────────────────────────────

def test_full_pipeline_inserts_all_companies(db, client_id):
    scrapers = [
        _mock_scraper("edgar", [_company("AlphaVenture LLC", "edgar")]),
        _mock_scraper("sbir",  [_company("DeepTech Corp", "sbir", 150_000)]),
        _mock_scraper("nih",   [_company("BioHeal Inc", "nih", 250_000)]),
    ]
    result = PipelineService(db, scrapers=scrapers, dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    assert result["total_scraped"] == 3
    assert result["after_dedup"] == 3
    assert result["new_companies"] == 3


def test_deduplication_within_batch(db, client_id):
    """Two scrapers returning the same name+source yields only one DB row."""
    scrapers = [
        _mock_scraper("edgar", [_company("DupeCo", "edgar")]),
        _mock_scraper("sbir",  [_company("DupeCo", "edgar")]),  # same name AND source
    ]
    result = PipelineService(db, scrapers=scrapers, dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    assert result["total_scraped"] == 2
    assert result["after_dedup"] == 1
    assert result["new_companies"] == 1


def test_same_name_different_source_is_not_deduped(db, client_id):
    """Same company name from two different sources = two separate rows."""
    scrapers = [
        _mock_scraper("edgar", [_company("Acme Corp", "edgar")]),
        _mock_scraper("sbir",  [_company("Acme Corp", "sbir")]),
    ]
    result = PipelineService(db, scrapers=scrapers, dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    assert result["new_companies"] == 2


def test_deduplication_against_existing_db_row(db, client_id):
    """A company already in the DB is not re-inserted."""
    db.add(Company(
        client_id=client_id,
        name="ExistingCo",
        sector="FinTech",
        stage="Seed",
        source="edgar",
        source_url="https://sec.gov/1",
        raw_data={},
    ))
    db.flush()

    scrapers = [_mock_scraper("edgar", [_company("ExistingCo", "edgar")])]
    result = PipelineService(db, scrapers=scrapers, dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    assert result["new_companies"] == 0
    count = db.query(Company).filter(
        Company.client_id == client_id,
        Company.name == "ExistingCo",
        Company.source == "edgar",
    ).count()
    assert count == 1  # still exactly one row


def test_pipeline_run_logged_on_success(db, client_id):
    scrapers = [_mock_scraper("edgar", [_company("LoggedCo", "edgar")])]
    result = PipelineService(db, scrapers=scrapers, dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    run = db.query(PipelineRun).filter(
        PipelineRun.id == uuid.UUID(result["pipeline_run_id"])
    ).one()

    assert run.status == "completed"
    assert run.companies_found == 1
    assert run.completed_at is not None
    assert run.client_id == client_id


def test_scraper_error_does_not_abort_pipeline(db, client_id):
    """A failing scraper is recorded in scraper_errors; remaining scrapers still run."""
    failing = MagicMock()
    failing.source = "edgar"
    failing.run.side_effect = RuntimeError("network timeout")

    working = _mock_scraper("sbir", [_company("WorkingCo", "sbir")])

    result = PipelineService(db, scrapers=[failing, working], dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    assert result["new_companies"] == 1
    assert len(result["scraper_errors"]) == 1
    assert "edgar" in result["scraper_errors"][0]
    assert "network timeout" in result["scraper_errors"][0]


def test_pipeline_run_records_partial_errors(db, client_id):
    """error_message on PipelineRun contains scraper failures when run otherwise succeeds."""
    failing = MagicMock()
    failing.source = "github"
    failing.run.side_effect = ConnectionError("rate limited")

    result = PipelineService(db, scrapers=[failing], dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    run = db.query(PipelineRun).filter(
        PipelineRun.id == uuid.UUID(result["pipeline_run_id"])
    ).one()
    assert run.status == "completed"
    assert "github" in run.error_message


def test_summary_dict_has_expected_keys(db, client_id):
    result = PipelineService(db, scrapers=[], dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    assert set(result.keys()) == {
        "pipeline_run_id",
        "total_scraped",
        "after_dedup",
        "new_companies",
        "scraper_errors",
    }


def test_empty_pipeline_run_logged(db, client_id):
    """Zero scrapers still creates a completed PipelineRun with companies_found=0."""
    result = PipelineService(db, scrapers=[], dispatch_scoring=lambda *a: None).run_full_pipeline(client_id)

    assert result["new_companies"] == 0
    run = db.query(PipelineRun).filter(
        PipelineRun.id == uuid.UUID(result["pipeline_run_id"])
    ).one()
    assert run.status == "completed"
    assert run.companies_found == 0


def test_client_id_isolation(db):
    """Companies inserted for client A are invisible to client B's dedup check."""
    client_a = Client(name="Client A", thesis_json={}, config_json={})
    client_b = Client(name="Client B", thesis_json={}, config_json={})
    db.add_all([client_a, client_b])
    db.flush()

    company_data = [_company("SharedName", "edgar")]

    _no_dispatch = lambda *a: None
    PipelineService(db, scrapers=[_mock_scraper("edgar", company_data)], dispatch_scoring=_no_dispatch).run_full_pipeline(client_a.id)
    result_b = PipelineService(db, scrapers=[_mock_scraper("edgar", company_data)], dispatch_scoring=_no_dispatch).run_full_pipeline(client_b.id)

    # Same company for a different client must be inserted — not treated as duplicate
    assert result_b["new_companies"] == 1

    assert db.query(Company).filter(Company.client_id == client_a.id).count() == 1
    assert db.query(Company).filter(Company.client_id == client_b.id).count() == 1
