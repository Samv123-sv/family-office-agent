from unittest.mock import MagicMock, patch

import pytest

from models.client import Client
from models.company import Company
from models.document import Document
from services.document_service import DocumentService


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def fo_client(db):
    c = Client(name="Summit FO", thesis_json={}, config_json={})
    db.add(c)
    db.flush()
    return c


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


# ── tests ─────────────────────────────────────────────────────────────────────

def test_ingest_plain_text_extracts_content(db, fo_client):
    content = "This is the deal memo for Acme AI."
    service = DocumentService(db)
    doc = service.ingest_document(
        client_id=fo_client.id,
        data=content.encode(),
        filename="memo.txt",
        file_type="text/plain",
    )
    assert doc.content_text == content
    assert doc.filename == "memo.txt"
    assert doc.file_type == "text/plain"
    assert doc.client_id == fo_client.id
    assert doc.company_id is None


def test_ingest_links_to_company(db, fo_client, company):
    service = DocumentService(db)
    doc = service.ingest_document(
        client_id=fo_client.id,
        data=b"CIM content here",
        filename="cim.txt",
        file_type="text/plain",
        company_id=company.id,
    )
    assert doc.company_id == company.id


def test_ingest_persists_to_db(db, fo_client):
    service = DocumentService(db)
    result = service.ingest_document(
        client_id=fo_client.id,
        data=b"Deal teaser text",
        filename="teaser.txt",
        file_type="text/plain",
    )
    persisted = db.query(Document).filter(Document.id == result.id).one()
    assert persisted.content_text == "Deal teaser text"
    assert persisted.client_id == fo_client.id


def test_ingest_pdf_extracts_via_fitz(db, fo_client):
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Page one content."
    mock_pdf = [mock_page]

    with patch("services.document_service.fitz") as mock_fitz:
        mock_fitz.open.return_value = mock_pdf
        service = DocumentService(db)
        doc = service.ingest_document(
            client_id=fo_client.id,
            data=b"%PDF-1.4 fake",
            filename="deal.pdf",
            file_type="application/pdf",
        )

    mock_fitz.open.assert_called_once_with(stream=b"%PDF-1.4 fake", filetype="pdf")
    assert doc.content_text == "Page one content."


def test_ingest_pdf_joins_multiple_pages(db, fo_client):
    pages = [MagicMock(), MagicMock()]
    pages[0].get_text.return_value = "Page one."
    pages[1].get_text.return_value = "Page two."

    with patch("services.document_service.fitz") as mock_fitz:
        mock_fitz.open.return_value = pages
        service = DocumentService(db)
        doc = service.ingest_document(
            client_id=fo_client.id,
            data=b"%PDF",
            filename="multi.pdf",
            file_type="application/pdf",
        )

    assert doc.content_text == "Page one.\nPage two."


def test_ingest_non_utf8_bytes_replaces_errors(db, fo_client):
    bad_bytes = b"Good text \xff bad byte"
    service = DocumentService(db)
    doc = service.ingest_document(
        client_id=fo_client.id,
        data=bad_bytes,
        filename="raw.txt",
        file_type="text/plain",
    )
    assert "Good text" in doc.content_text
    assert doc.content_text is not None


def test_ingest_multiple_documents_same_company(db, fo_client, company):
    service = DocumentService(db)
    for i in range(3):
        service.ingest_document(
            client_id=fo_client.id,
            data=f"Document {i}".encode(),
            filename=f"doc_{i}.txt",
            file_type="text/plain",
            company_id=company.id,
        )
    docs = db.query(Document).filter(Document.company_id == company.id).all()
    assert len(docs) == 3
