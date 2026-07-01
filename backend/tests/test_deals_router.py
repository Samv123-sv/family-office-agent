import uuid

import pytest

from models.client import Client
from models.company import Company
from models.memo import Memo
from models.score import Score


@pytest.fixture
def fo_client(db):
    c = Client(name="Summit FO", thesis_json={"sectors": ["SaaS"]}, config_json={})
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def auth_client_id(fo_client):
    return fo_client.id


@pytest.fixture
def company(db, fo_client):
    co = Company(
        client_id=fo_client.id,
        name="BrightStack AI",
        sector="SaaS",
        stage="Seed",
        source="hn_yc",
        source_url="https://example.com",
        raw_data={},
    )
    db.add(co)
    db.flush()
    return co


@pytest.fixture
def score(db, company, fo_client):
    s = Score(
        company_id=company.id,
        client_id=fo_client.id,
        total_score=7.5,
        dimension_scores={"thesis_fit": 8, "team_signals": 7, "market_timing": 8, "data_quality": 7},
        scoring_notes="Strong fit.",
        recommendation="REACH_OUT",
    )
    db.add(s)
    db.flush()
    return s


# ── GET /api/deals ────────────────────────────────────────────────────────────

def test_list_deals_returns_companies(api_client, company, score):
    resp = api_client.get("/api/deals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "BrightStack AI"
    assert body["items"][0]["score"]["total_score"] == 7.5
    assert body["items"][0]["score"]["recommendation"] == "REACH_OUT"


def test_list_deals_sector_filter_match(api_client, company, score):
    resp = api_client.get("/api/deals?sector=SaaS")
    assert resp.json()["total"] == 1


def test_list_deals_sector_filter_no_match(api_client, company, score):
    resp = api_client.get("/api/deals?sector=FinTech")
    assert resp.json()["total"] == 0


def test_list_deals_min_score_filter(api_client, company, score):
    resp = api_client.get("/api/deals?min_score=5.0")
    assert resp.json()["total"] == 1

    resp2 = api_client.get("/api/deals?min_score=9.0")
    assert resp2.json()["total"] == 0


def test_list_deals_recommendation_filter(api_client, company, score):
    resp = api_client.get("/api/deals?recommendation=REACH_OUT")
    assert resp.json()["total"] == 1

    resp2 = api_client.get("/api/deals?recommendation=PASS")
    assert resp2.json()["total"] == 0


def test_list_deals_pagination(api_client, fo_client, db):
    for i in range(25):
        db.add(Company(
            client_id=fo_client.id,
            name=f"Company {i}",
            sector="SaaS",
            stage="Seed",
            source="edgar",
            source_url=f"https://example.com/{i}",
            raw_data={},
        ))
    db.flush()

    resp = api_client.get("/api/deals?page=1&limit=10")
    body = resp.json()
    assert len(body["items"]) == 10
    assert body["total"] == 25
    assert body["pages"] == 3
    assert body["page"] == 1


def test_list_deals_empty(api_client):
    resp = api_client.get("/api/deals")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["items"] == []


# ── GET /api/deals/{company_id} ───────────────────────────────────────────────

def test_get_deal_detail_with_score(api_client, company, score):
    resp = api_client.get(f"/api/deals/{company.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "BrightStack AI"
    assert body["score"]["total_score"] == 7.5
    assert body["memo"] is None


def test_get_deal_detail_with_memo(api_client, fo_client, company, score, db):
    memo = Memo(
        company_id=company.id,
        client_id=fo_client.id,
        content="Test memo content",
        version=1,
    )
    db.add(memo)
    db.flush()

    resp = api_client.get(f"/api/deals/{company.id}")
    assert resp.status_code == 200
    assert resp.json()["memo"]["content"] == "Test memo content"


def test_get_deal_not_found(api_client):
    resp = api_client.get(f"/api/deals/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_deal_wrong_client_returns_403(make_api_client, company, fo_client, db):
    """Token belonging to a different client gets 403, not 404, on a specific deal."""
    other = Client(name="Other FO", thesis_json={}, config_json={})
    db.add(other)
    db.flush()

    resp = make_api_client(other.id).get(f"/api/deals/{company.id}")
    assert resp.status_code == 403
