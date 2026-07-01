import pytest

from models.alert import Alert
from models.client import Client
from models.company import Company


@pytest.fixture
def fo_client(db):
    c = Client(name="Apex Capital", thesis_json={}, config_json={})
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
        name="Acme AI",
        sector="AI/ML",
        stage="Seed",
        source="github",
        source_url="https://github.com/acme",
        raw_data={},
    )
    db.add(co)
    db.flush()
    return co


@pytest.fixture
def alerts(db, fo_client, company):
    rows = [
        Alert(client_id=fo_client.id, company_id=company.id, channel="sms", message=f"Alert {i}")
        for i in range(3)
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_list_alerts_returns_client_alerts(api_client, alerts):
    resp = api_client.get("/api/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert all(r["channel"] == "sms" for r in data)


def test_list_alerts_empty_when_none(api_client):
    resp = api_client.get("/api/alerts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_alerts_limit(api_client, alerts):
    resp = api_client.get("/api/alerts?limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_alerts_excludes_other_client(db, api_client, company):
    other = Client(name="Other FO", thesis_json={}, config_json={})
    db.add(other)
    db.flush()
    db.add(Alert(client_id=other.id, company_id=company.id, channel="sms", message="Other alert"))
    db.commit()

    resp = api_client.get("/api/alerts")
    assert resp.status_code == 200
    assert resp.json() == []
