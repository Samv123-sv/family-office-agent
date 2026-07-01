from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import db.queries as queries
from auth.clerk import get_authenticated_client
from database import get_db
from models.company import Company
from schemas import MemoResponse
from services.memo_service import MemoService

router = APIRouter(tags=["memos"])


@router.post("/deals/{company_id}/memo", response_model=MemoResponse)
def generate_memo(
    company_id: UUID,
    client_id: UUID = Depends(get_authenticated_client),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company.client_id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = MemoService(db).generate_memo(company_id, client_id)
    return MemoResponse(**result)
