import uuid

import pytest

from models.client import Client

_THESIS = {"sectors": ["SaaS", "FinTech"], "stages": ["Seed"], "geography": ["US"]}
_CONFIG = {"notify_email": True}


@pytest.fixture
def fo_client(db):
    c = Client(name="Summit FO", thesis_json=_THESIS, config_json=_CONFIG)
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def auth_client_id(fo_client):
    return fo_client.id


def test_get_thesis(api_client, fo_client):
    resp = api_client.get("/api/thesis")
    assert resp.status_code == 200
    body = resp.json()
    assert body["thesis_json"] == _THESIS
    assert body["config_json"] == _CONFIG
    assert body["name"] == "Summit FO"


def test_get_thesis_not_found(make_api_client):
    """Auth token with a client_id that has no DB record → 404."""
    resp = make_api_client(uuid.uuid4()).get("/api/thesis")
    assert resp.status_code == 404


def test_put_thesis_updates_fields(api_client, fo_client):
    new_thesis = {"sectors": ["CleanTech"], "stages": ["Series B"], "geography": ["EU"]}
    new_config = {"notify_slack": True}

    resp = api_client.put("/api/thesis", json={
        "thesis_json": new_thesis,
        "config_json": new_config,
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["thesis_json"] == new_thesis
    assert body["config_json"] == new_config


def test_put_thesis_persists_to_db(api_client, fo_client, db):
    new_thesis = {"sectors": ["DeepTech"]}
    api_client.put("/api/thesis", json={
        "thesis_json": new_thesis,
        "config_json": {},
    })

    db.refresh(fo_client)
    assert fo_client.thesis_json == new_thesis


def test_put_thesis_not_found(make_api_client):
    """Auth with unknown client_id → 404 on PUT."""
    resp = make_api_client(uuid.uuid4()).put("/api/thesis", json={
        "thesis_json": {},
        "config_json": {},
    })
    assert resp.status_code == 404


def test_put_thesis_missing_field(api_client, fo_client):
    """Missing config_json → 422 validation error."""
    resp = api_client.put("/api/thesis", json={"thesis_json": {}})
    assert resp.status_code == 422
