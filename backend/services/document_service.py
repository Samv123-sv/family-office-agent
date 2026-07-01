import logging
from uuid import UUID

import fitz
from sqlalchemy.orm import Session

from models.document import Document

logger = logging.getLogger(__name__)

_PLAIN_TEXT_TYPES = {"text/plain", "text/csv", "text/markdown"}


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_document(
        self,
        client_id: UUID,
        data: bytes,
        filename: str,
        file_type: str,
        company_id: UUID | None = None,
    ) -> Document:
        content_text = self._extract_text(data, file_type)
        doc = Document(
            client_id=client_id,
            company_id=company_id,
            filename=filename,
            file_type=file_type,
            content_text=content_text,
        )
        self.db.add(doc)
        self.db.commit()
        logger.info("document ingested client=%s filename=%s bytes=%d", client_id, filename, len(data))
        return doc

    def _extract_text(self, data: bytes, file_type: str) -> str:
        if file_type == "application/pdf":
            pdf = fitz.open(stream=data, filetype="pdf")
            return "\n".join(page.get_text() for page in pdf)
        return data.decode("utf-8", errors="replace")
