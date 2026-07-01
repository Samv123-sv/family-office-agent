from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.clerk import get_authenticated_client
from database import get_db
from db import queries
from schemas import AlertResponse

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(
    limit: int = Query(20, ge=1, le=100),
    client_id: UUID = Depends(get_authenticated_client),
    db: Session = Depends(get_db),
):
    return queries.list_alerts(db, client_id, limit=limit)
