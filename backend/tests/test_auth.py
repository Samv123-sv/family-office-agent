"""
Cross-tenant isolation tests.
These verify that a valid token for client A cannot read or modify client B's data.
"""
import uuid

import pytest

from models.client import Client
from models.company import Company


@pytest.fixture
def client_a(db):
    c = Client(name="Alpha FO", thesis_json={"sectors": ["SaaS"]}, config_json={})
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def client_b(db):
    c = Client(name="Beta FO", thesis_json={"sectors": ["FinTech"]}, config_json={})
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def company_b(db, client_b):
    co = Company(
        client_id=client_b.id,
        name="BetaStack Inc",
        sector="FinTech",
        stage="Seed",
        source="hn_yc",
        source_url="https://example.com/b",
        raw_data={},
    )
    db.add(co)
    db.flush()
    return co


def test_client_a_cannot_access_client_b_deal(make_api_client, client_a, company_b):
    """GET /deals/{id} returns 403 when the resource belongs to another client."""
    resp = make_api_client(client_a.id).get(f"/api/deals/{company_b.id}")
    assert resp.status_code == 403


def test_client_a_deal_list_excludes_client_b_companies(make_api_client, client_a, client_b, db):
    """GET /deals list only returns the authenticated client's companies."""
    db.add(Company(
        client_id=client_a.id, name="Alpha Deal",
        sector="SaaS", stage="Seed", source="hn_yc",
        source_url="https://a.com", raw_data={},
    ))
    db.add(Company(
        client_id=client_b.id, name="Beta Deal",
        sector="FinTech", stage="Seed", source="hn_yc",
        source_url="https://b.com", raw_data={},
    ))
    db.flush()

    resp = make_api_client(client_a.id).get("/api/deals")
    assert resp.status_code == 200
    names = [item["name"] for item in resp.json()["items"]]
    assert "Alpha Deal" in names
    assert "Beta Deal" not in names


def test_client_a_cannot_generate_memo_for_client_b_company(make_api_client, client_a, company_b):
    """POST /deals/{id}/memo returns 403 for a company owned by another client."""
    resp = make_api_client(client_a.id).post(f"/api/deals/{company_b.id}/memo")
    assert resp.status_code == 403


def test_client_a_thesis_update_does_not_affect_client_b(make_api_client, client_a, client_b, db):
    """PUT /thesis only modifies the authenticated client's record."""
    make_api_client(client_a.id).put("/api/thesis", json={
        "thesis_json": {"sectors": ["AI"]},
        "config_json": {},
    })

    db.refresh(client_b)
    assert client_b.thesis_json == {"sectors": ["FinTech"]}


def test_unregistered_client_id_returns_404_on_thesis(make_api_client):
    """A client_id with no DB record causes a 404 on endpoints that look up the client."""
    resp = make_api_client(uuid.uuid4()).get("/api/thesis")
    assert resp.status_code == 404
