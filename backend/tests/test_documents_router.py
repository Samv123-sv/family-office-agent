import io

import pytest

from models.client import Client
from models.company import Company
from models.document import Document


# ── fixtures ──────────────────────────────────────────────────────────────────

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


def _upload(api_client, content: bytes, filename: str, company_id=None):
    data = {"file": (filename, io.BytesIO(content), "text/plain")}
    if company_id:
        data["company_id"] = (None, str(company_id))
    return api_client.post("/api/documents", files=data)


# ── upload tests ──────────────────────────────────────────────────────────────

def test_upload_plain_text_returns_201(api_client):
    resp = _upload(api_client, b"Deal teaser content", "teaser.txt")
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "teaser.txt"
    assert "id" in body


def test_upload_with_company_id_links_document(api_client, company):
    resp = _upload(api_client, b"CIM content", "cim.txt", company_id=company.id)
    assert resp.status_code == 201
    assert resp.json()["company_id"] == str(company.id)


def test_upload_without_company_id_has_null_company(api_client):
    resp = _upload(api_client, b"Generic doc", "doc.txt")
    assert resp.status_code == 201
    assert resp.json()["company_id"] is None


def test_upload_persists_to_db(api_client, db, fo_client):
    _upload(api_client, b"Persisted content", "persist.txt")
    doc = db.query(Document).filter(Document.client_id == fo_client.id).first()
    assert doc is not None
    assert doc.content_text == "Persisted content"


def test_upload_wrong_client_company_returns_403(db, api_client):
    other = Client(name="Other FO", thesis_json={}, config_json={})
    db.add(other)
    db.flush()
    other_co = Company(
        client_id=other.id,
        name="Other Co",
        sector="SaaS",
        stage="Seed",
        source="github",
        source_url="https://github.com/other",
        raw_data={},
    )
    db.add(other_co)
    db.flush()

    resp = _upload(api_client, b"Attempt", "file.txt", company_id=other_co.id)
    assert resp.status_code == 403


def test_upload_nonexistent_company_returns_404(api_client):
    import uuid
    resp = _upload(api_client, b"Attempt", "file.txt", company_id=uuid.uuid4())
    assert resp.status_code == 404


# ── list tests ────────────────────────────────────────────────────────────────

def test_list_documents_returns_uploaded(api_client, company):
    _upload(api_client, b"Doc A", "a.txt", company_id=company.id)
    _upload(api_client, b"Doc B", "b.txt", company_id=company.id)

    resp = api_client.get(f"/api/documents?company_id={company.id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    filenames = {d["filename"] for d in resp.json()}
    assert filenames == {"a.txt", "b.txt"}


def test_list_documents_empty_when_none(api_client, company):
    resp = api_client.get(f"/api/documents?company_id={company.id}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_documents_wrong_client_returns_403(db, api_client):
    other = Client(name="Other FO", thesis_json={}, config_json={})
    db.add(other)
    db.flush()
    other_co = Company(
        client_id=other.id,
        name="Other Co",
        sector="SaaS",
        stage="Seed",
        source="github",
        source_url="https://github.com/other",
        raw_data={},
    )
    db.add(other_co)
    db.flush()

    resp = api_client.get(f"/api/documents?company_id={other_co.id}")
    assert resp.status_code == 403
