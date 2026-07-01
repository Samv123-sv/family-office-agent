import json
import uuid
from unittest.mock import MagicMock

import pytest

from models.client import Client
from models.company import Company
from models.score import Score
from services.scoring_service import ScoringService

_THESIS = {
    "sectors": ["SaaS", "FinTech"],
    "stages": ["Seed", "Series A"],
    "geography": ["US"],
    "check_size": {"min": 500_000, "max": 5_000_000},
}

_MOCK_SCORE = {
    "total_score": 7.5,
    "dimension_scores": {
        "thesis_fit": 8,
        "team_signals": 7,
        "market_timing": 8,
        "data_quality": 7,
    },
    "scoring_notes": "Strong thesis alignment with SaaS focus. Founding team has prior exits. Market timing is favorable given current FinTech tailwinds.",
    "recommendation": "REACH_OUT",
}


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client_id(db):
    client = Client(name="Summit FO", thesis_json=_THESIS, config_json={})
    db.add(client)
    db.flush()
    return client.id


@pytest.fixture
def company_id(db, client_id):
    company = Company(
        client_id=client_id,
        name="BrightStack AI",
        sector="SaaS",
        stage="Seed",
        funding_total=None,
        latest_round_size=2_000_000.0,
        source="hn_yc",
        source_url="https://news.ycombinator.com/item?id=12345",
        raw_data={"description": "AI-powered SaaS analytics platform"},
    )
    db.add(company)
    db.flush()
    return company.id


def _mock_claude(response: dict) -> MagicMock:
    mock = MagicMock()
    mock.messages.create.return_value.content = [MagicMock(text=json.dumps(response))]
    return mock


# ── tests ─────────────────────────────────────────────────────────────────────

def test_score_company_returns_expected_keys(db, company_id, client_id):
    service = ScoringService(db, anthropic_client=_mock_claude(_MOCK_SCORE))
    result = service.score_company(company_id, client_id)

    assert set(result.keys()) == {
        "score_id", "company_id", "client_id",
        "total_score", "dimension_scores", "scoring_notes", "recommendation",
    }


def test_score_company_values(db, company_id, client_id):
    service = ScoringService(db, anthropic_client=_mock_claude(_MOCK_SCORE))
    result = service.score_company(company_id, client_id)

    assert result["total_score"] == 7.5
    assert result["recommendation"] == "REACH_OUT"
    assert result["dimension_scores"]["thesis_fit"] == 8
    assert result["company_id"] == str(company_id)
    assert result["client_id"] == str(client_id)


def test_score_written_to_db(db, company_id, client_id):
    service = ScoringService(db, anthropic_client=_mock_claude(_MOCK_SCORE))
    result = service.score_company(company_id, client_id)

    score = db.query(Score).filter(Score.id == uuid.UUID(result["score_id"])).one()
    assert score.total_score == 7.5
    assert score.company_id == company_id
    assert score.client_id == client_id
    assert score.dimension_scores["market_timing"] == 8
    assert "FinTech" in score.scoring_notes


def test_claude_called_with_thesis_and_company(db, company_id, client_id):
    mock_claude = _mock_claude(_MOCK_SCORE)
    service = ScoringService(db, anthropic_client=mock_claude)
    service.score_company(company_id, client_id)

    mock_claude.messages.create.assert_called_once()
    call_kwargs = mock_claude.messages.create.call_args
    prompt_content = call_kwargs.kwargs["messages"][0]["content"]

    assert "BrightStack AI" in prompt_content
    assert "SaaS" in prompt_content
    assert "Summit FO" not in prompt_content  # client name not in prompt, but thesis is
    assert json.dumps(_THESIS["sectors"]) in prompt_content or "SaaS" in prompt_content


def test_parse_response_strips_markdown_fences(db, company_id, client_id):
    """Claude sometimes wraps JSON in ```json ... ``` — service must handle it."""
    fenced = f"```json\n{json.dumps(_MOCK_SCORE)}\n```"
    mock_claude = MagicMock()
    mock_claude.messages.create.return_value.content = [MagicMock(text=fenced)]

    service = ScoringService(db, anthropic_client=mock_claude)
    result = service.score_company(company_id, client_id)

    assert result["total_score"] == 7.5


def test_multitenant_wrong_client_raises(db, company_id, client_id):
    """Querying a company with the wrong client_id must raise (not return another client's data)."""
    wrong_client = Client(name="Other FO", thesis_json={}, config_json={})
    db.add(wrong_client)
    db.flush()

    service = ScoringService(db, anthropic_client=_mock_claude(_MOCK_SCORE))
    with pytest.raises(Exception):
        service.score_company(company_id, wrong_client.id)


def test_dispatch_is_called_for_each_new_company(db, client_id):
    """PipelineService calls dispatch_scoring once per new company."""
    from unittest.mock import MagicMock as MM
    from models.client import Client
    from services.pipeline_service import PipelineService

    dispatched = []

    def _company(name, source):
        return {
            "name": name, "sector": "SaaS", "stage": "Seed",
            "funding_total": None, "latest_round_size": None,
            "source": source, "source_url": "https://example.com", "raw_data": {},
        }

    scraper = MM()
    scraper.source = "edgar"
    scraper.run.return_value = [_company("NewCo A", "edgar"), _company("NewCo B", "edgar")]

    PipelineService(
        db,
        scrapers=[scraper],
        dispatch_scoring=lambda cid, kid: dispatched.append((cid, kid)),
    ).run_full_pipeline(client_id)

    assert len(dispatched) == 2
    # Each dispatch carries a valid UUID string
    for company_uuid, cid in dispatched:
        assert uuid.UUID(company_uuid)
        assert str(client_id) == cid
