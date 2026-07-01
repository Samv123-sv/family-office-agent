import uuid
from datetime import datetime, timezone
from sqlalchemy import inspect

from models.client import Client
from models.company import Company
from models.score import Score
from models.memo import Memo
from models.pipeline_run import PipelineRun


# ── column presence ──────────────────────────────────────────────────────────

def _cols(model):
    return {c.key for c in inspect(model).mapper.column_attrs}


def test_client_columns():
    assert _cols(Client) == {"id", "name", "clerk_org_id", "thesis_json", "config_json", "created_at"}


def test_company_columns():
    assert _cols(Company) == {
        "id", "client_id", "name", "sector", "stage",
        "funding_total", "latest_round_size", "source", "source_url",
        "raw_data", "created_at",
    }


def test_score_columns():
    assert _cols(Score) == {
        "id", "company_id", "client_id", "total_score",
        "dimension_scores", "scoring_notes", "recommendation", "scored_at",
    }


def test_memo_columns():
    assert _cols(Memo) == {
        "id", "company_id", "client_id", "content", "version", "generated_at",
    }


def test_pipeline_run_columns():
    assert _cols(PipelineRun) == {
        "id", "client_id", "source", "status", "companies_found",
        "error_message", "started_at", "completed_at",
    }


# ── every table has client_id ────────────────────────────────────────────────

def test_all_tables_have_client_id():
    for model in (Company, Score, Memo, PipelineRun):
        assert "client_id" in _cols(model), f"{model.__tablename__} missing client_id"


# ── defaults and nullable rules ──────────────────────────────────────────────

def test_client_defaults(db):
    client = Client(name="Acme Capital", thesis_json={}, config_json={})
    db.add(client)
    db.flush()

    assert isinstance(client.id, uuid.UUID)
    assert isinstance(client.created_at, datetime)
    assert client.thesis_json == {}


def test_company_nullable_funding(db):
    client_id = uuid.uuid4()
    company = Company(
        client_id=client_id,
        name="TestCo",
        sector="FinTech",
        stage="Series A",
        source="crunchbase",
        source_url="https://crunchbase.com/testco",
        raw_data={},
    )
    assert company.funding_total is None
    assert company.latest_round_size is None


def test_memo_version_default(db):
    memo = Memo(
        company_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        content="This is a test memo.",
    )
    db.add(memo)
    db.flush()
    assert memo.version == 1


def test_pipeline_run_completed_at_nullable(db):
    run = PipelineRun(
        client_id=uuid.uuid4(),
        source="crunchbase",
        status="running",
    )
    assert run.completed_at is None
    assert run.error_message is None


# ── integration: insert and retrieve ────────────────────────────────────────

def test_insert_client(db):
    client = Client(
        name="Summit Family Office",
        thesis_json={"sectors": ["SaaS", "FinTech"], "stages": ["Series A", "Series B"]},
        config_json={"notify_email": True},
    )
    db.add(client)
    db.flush()

    fetched = db.get(Client, client.id)
    assert fetched.name == "Summit Family Office"
    assert fetched.thesis_json["sectors"] == ["SaaS", "FinTech"]


def test_insert_full_pipeline(db):
    client = Client(name="Peak Capital", thesis_json={}, config_json={})
    db.add(client)
    db.flush()

    company = Company(
        client_id=client.id,
        name="BrightStar AI",
        sector="AI/ML",
        stage="Seed",
        funding_total=2_500_000.0,
        latest_round_size=2_500_000.0,
        source="crunchbase",
        source_url="https://crunchbase.com/brightstar",
        raw_data={"description": "AI-powered analytics"},
    )
    db.add(company)
    db.flush()

    score = Score(
        company_id=company.id,
        client_id=client.id,
        total_score=82.5,
        dimension_scores={
            "thesis_fit": 90,
            "team_signals": 80,
            "market_timing": 85,
            "data_quality": 75,
        },
        scoring_notes="Strong thesis alignment. Founder previously exited at Series C.",
    )
    db.add(score)

    memo = Memo(
        company_id=company.id,
        client_id=client.id,
        content="## BrightStar AI\n\nStrong seed-stage AI company...",
    )
    db.add(memo)

    run = PipelineRun(
        client_id=client.id,
        source="crunchbase",
        status="completed",
        companies_found=1,
    )
    db.add(run)
    db.flush()

    assert score.total_score == 82.5
    assert memo.version == 1
    assert run.companies_found == 1
    assert run.completed_at is None  # not yet set
