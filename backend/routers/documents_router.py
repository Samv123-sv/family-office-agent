from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

import db.queries as queries
from auth.clerk import get_authenticated_client
from database import get_db
from models.company import Company
from schemas import DocumentResponse
from services.document_service import DocumentService

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    company_id: str | None = Form(None),
    client_id: UUID = Depends(get_authenticated_client),
    db: Session = Depends(get_db),
):
    cid: UUID | None = None
    if company_id:
        cid = UUID(company_id)
        company = db.query(Company).filter(Company.id == cid).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        if company.client_id != client_id:
            raise HTTPException(status_code=403, detail="Access denied")

    data = await file.read()
    service = DocumentService(db)
    return service.ingest_document(
        client_id=client_id,
        data=data,
        filename=file.filename or "upload",
        file_type=file.content_type or "application/octet-stream",
        company_id=cid,
    )


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    company_id: UUID = Query(...),
    client_id: UUID = Depends(get_authenticated_client),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company.client_id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return queries.list_documents_for_company(db, company_id, client_id)
