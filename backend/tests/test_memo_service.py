import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from models.client import Client
from models.company import Company
from models.memo import Memo
from models.score import Score
from services.memo_service import MemoService

_THESIS = {
    "sectors": ["SaaS", "FinTech"],
    "stages": ["Seed", "Series A"],
    "geography": ["US"],
    "check_size": {"min": 500_000, "max": 5_000_000},
    "keywords": ["AI", "enterprise"],
}

_MEMO_CONTENT = """COMPANY OVERVIEW
BrightStack AI is an AI-powered analytics platform founded in 2023 in San Francisco.

FUNDING HISTORY
Raised $2M seed from YC and angels.

THESIS ALIGNMENT
Strong alignment with SaaS and FinTech focus. Seed stage matches criteria.

KEY RISKS
1. Early revenue. 2. Crowded market. 3. Founder concentration risk.

RECOMMENDED NEXT STEP
REACH OUT — request product demo with CTO.

SOURCES
- https://news.ycombinator.com/item?id=12345""".strip()


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client(db):
    c = Client(name="Summit FO", thesis_json=_THESIS, config_json={})
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def company(db, client):
    co = Company(
        client_id=client.id,
        name="BrightStack AI",
        sector="SaaS",
        stage="Seed",
        funding_total=None,
        latest_round_size=2_000_000.0,
        source="hn_yc",
        source_url="https://news.ycombinator.com/item?id=12345",
        raw_data={"description": "AI analytics SaaS"},
    )
    db.add(co)
    db.flush()
    return co


@pytest.fixture
def score(db, company, client):
    s = Score(
        company_id=company.id,
        client_id=client.id,
        total_score=7.5,
        dimension_scores={"thesis_fit": 8, "team_signals": 7, "market_timing": 8, "data_quality": 7},
        scoring_notes="Strong thesis alignment. Founder previously exited.",
    )
    db.add(s)
    db.flush()
    return s


def _mock_claude(content: str = _MEMO_CONTENT) -> MagicMock:
    mock = MagicMock()
    mock.messages.create.return_value.content = [MagicMock(text=content)]
    return mock


# ── tests ─────────────────────────────────────────────────────────────────────

def test_generate_memo_returns_expected_keys(db, company, client, score):
    service = MemoService(db, anthropic_client=_mock_claude())
    result = service.generate_memo(company.id, client.id)

    assert set(result.keys()) == {
        "memo_id", "company_id", "client_id",
        "content", "version", "generated_at", "cached",
    }


def test_generate_memo_content_and_version(db, company, client, score):
    service = MemoService(db, anthropic_client=_mock_claude())
    result = service.generate_memo(company.id, client.id)

    assert result["content"] == _MEMO_CONTENT
    assert result["version"] == 1
    assert result["cached"] is False
    assert result["company_id"] == str(company.id)
    assert result["client_id"] == str(client.id)


def test_memo_written_to_db(db, company, client, score):
    service = MemoService(db, anthropic_client=_mock_claude())
    result = service.generate_memo(company.id, client.id)

    memo = db.query(Memo).filter(Memo.id == uuid.UUID(result["memo_id"])).one()
    assert memo.content == _MEMO_CONTENT
    assert memo.version == 1
    assert memo.company_id == company.id
    assert memo.client_id == client.id


def test_cache_hit_skips_claude(db, company, client):
    """Memo generated less than 7 days ago is returned without calling Claude."""
    existing = Memo(
        company_id=company.id,
        client_id=client.id,
        content="Cached memo content",
        version=1,
        generated_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db.add(existing)
    db.commit()

    mock_claude = _mock_claude()
    service = MemoService(db, anthropic_client=mock_claude)
    result = service.generate_memo(company.id, client.id)

    mock_claude.messages.create.assert_not_called()
    assert result["cached"] is True
    assert result["content"] == "Cached memo content"


def test_cache_miss_regenerates_after_7_days(db, company, client, score):
    """Memo older than 7 days triggers a new generation and increments version."""
    old = Memo(
        company_id=company.id,
        client_id=client.id,
        content="Old memo",
        version=1,
        generated_at=datetime.now(timezone.utc) - timedelta(days=8),
    )
    db.add(old)
    db.commit()

    service = MemoService(db, anthropic_client=_mock_claude())
    result = service.generate_memo(company.id, client.id)

    assert result["cached"] is False
    assert result["version"] == 2
    assert result["content"] == _MEMO_CONTENT


def test_version_increments_on_each_generation(db, company, client, score):
    """Each forced regeneration bumps the version number."""
    for expected_version in range(1, 4):
        # Each call has no recent cache (pass old generated_at via direct insert)
        service = MemoService(db, anthropic_client=_mock_claude())
        # Expire any existing fresh memos so cache is always cold
        db.query(Memo).filter(Memo.company_id == company.id).update(
            {"generated_at": datetime.now(timezone.utc) - timedelta(days=8)}
        )
        db.commit()
        result = service.generate_memo(company.id, client.id)
        assert result["version"] == expected_version


def test_claude_prompt_contains_thesis_and_company(db, company, client, score):
    mock_claude = _mock_claude()
    service = MemoService(db, anthropic_client=mock_claude)
    service.generate_memo(company.id, client.id)

    prompt = mock_claude.messages.create.call_args.kwargs["messages"][0]["content"]

    assert "Summit FO" in prompt
    assert "BrightStack AI" in prompt
    assert "SaaS" in prompt
    assert "7.5" in prompt
    assert "Strong thesis alignment" in prompt


def test_memo_without_score_uses_fallback(db, company, client):
    """generate_memo works even when no score exists yet."""
    service = MemoService(db, anthropic_client=_mock_claude())
    result = service.generate_memo(company.id, client.id)

    prompt = service._build_prompt(company, client, score=None)
    assert "Not yet scored" in prompt
    assert result["content"] == _MEMO_CONTENT


def test_multitenant_wrong_client_raises(db, company, client, score):
    wrong_client = Client(name="Other FO", thesis_json={}, config_json={})
    db.add(wrong_client)
    db.flush()

    service = MemoService(db, anthropic_client=_mock_claude())
    with pytest.raises(Exception):
        service.generate_memo(company.id, wrong_client.id)


# ── document context ──────────────────────────────────────────────────────────

def test_prompt_includes_document_excerpts(db, company, client, score):
    from models.document import Document
    doc = Document(
        client_id=client.id,
        company_id=company.id,
        filename="cim.txt",
        file_type="text/plain",
        content_text="Revenue: $5M ARR. 120% net revenue retention. CEO previously founded Acme Corp (acquired 2021).",
    )
    db.add(doc)
    db.commit()

    mock_claude = _mock_claude()
    service = MemoService(db, anthropic_client=mock_claude)
    service.generate_memo(company.id, client.id)

    prompt = mock_claude.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "ADDITIONAL CONTEXT FROM CLIENT DOCUMENTS:" in prompt
    assert "cim.txt" in prompt
    assert "$5M ARR" in prompt


def test_prompt_without_documents_has_no_context_section(db, company, client, score):
    mock_claude = _mock_claude()
    service = MemoService(db, anthropic_client=mock_claude)
    service.generate_memo(company.id, client.id)

    prompt = mock_claude.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "ADDITIONAL CONTEXT FROM CLIENT DOCUMENTS:" not in prompt


def test_document_excerpt_truncated_to_2000_chars(db, company, client, score):
    from models.document import Document
    long_text = "X" * 5000
    doc = Document(
        client_id=client.id,
        company_id=company.id,
        filename="long.txt",
        file_type="text/plain",
        content_text=long_text,
    )
    db.add(doc)
    db.commit()

    mock_claude = _mock_claude()
    service = MemoService(db, anthropic_client=mock_claude)
    service.generate_memo(company.id, client.id)

    prompt = mock_claude.messages.create.call_args.kwargs["messages"][0]["content"]
    # The full 5000 chars should NOT appear — excerpt is capped at 2000
    assert "X" * 2001 not in prompt
    assert "X" * 2000 in prompt


def test_multiple_documents_all_appear_in_prompt(db, company, client, score):
    from models.document import Document
    for i, fname in enumerate(["a.txt", "b.txt"]):
        db.add(Document(
            client_id=client.id,
            company_id=company.id,
            filename=fname,
            file_type="text/plain",
            content_text=f"Content from {fname}",
        ))
    db.commit()

    mock_claude = _mock_claude()
    service = MemoService(db, anthropic_client=mock_claude)
    service.generate_memo(company.id, client.id)

    prompt = mock_claude.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "a.txt" in prompt
    assert "b.txt" in prompt
    assert "Content from a.txt" in prompt
    assert "Content from b.txt" in prompt
