import uuid
from unittest.mock import patch

import pytest

from models.client import Client
from models.company import Company


@pytest.fixture
def fo_client(db):
    c = Client(name="Summit FO", thesis_json={}, config_json={})
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


_MOCK_MEMO = {
    "memo_id": str(uuid.uuid4()),
    "company_id": str(uuid.uuid4()),
    "client_id": str(uuid.uuid4()),
    "content": "COMPANY OVERVIEW\nTest company overview.",
    "version": 1,
    "generated_at": "2026-06-27T10:00:00+00:00",
    "cached": False,
}


def test_generate_memo_success(api_client, company):
    with patch("routers.memos_router.MemoService") as MockService:
        MockService.return_value.generate_memo.return_value = _MOCK_MEMO
        resp = api_client.post(f"/api/deals/{company.id}/memo")

    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == _MOCK_MEMO["content"]
    assert body["version"] == 1
    assert body["cached"] is False


def test_generate_memo_company_not_found(api_client, fo_client):
    resp = api_client.post(f"/api/deals/{uuid.uuid4()}/memo")
    assert resp.status_code == 404


def test_generate_memo_wrong_client_returns_403(make_api_client, company, fo_client, db):
    """A token for a different client cannot generate a memo for another client's company."""
    other = Client(name="Other FO", thesis_json={}, config_json={})
    db.add(other)
    db.flush()

    resp = make_api_client(other.id).post(f"/api/deals/{company.id}/memo")
    assert resp.status_code == 403


def test_generate_memo_cached_returns_cached_flag(api_client, company):
    cached_memo = {**_MOCK_MEMO, "cached": True, "version": 2}
    with patch("routers.memos_router.MemoService") as MockService:
        MockService.return_value.generate_memo.return_value = cached_memo
        resp = api_client.post(f"/api/deals/{company.id}/memo")

    assert resp.status_code == 200
    assert resp.json()["cached"] is True
    assert resp.json()["version"] == 2
