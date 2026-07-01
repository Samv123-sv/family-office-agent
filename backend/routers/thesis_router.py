from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import db.queries as queries
from auth.clerk import get_authenticated_client
from database import get_db
from schemas import ClientResponse, ThesisUpdateRequest

router = APIRouter(tags=["thesis"])


@router.get("/thesis", response_model=ClientResponse)
def get_thesis(
    client_id: UUID = Depends(get_authenticated_client),
    db: Session = Depends(get_db),
):
    client = queries.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.put("/thesis", response_model=ClientResponse)
def update_thesis(
    body: ThesisUpdateRequest,
    client_id: UUID = Depends(get_authenticated_client),
    db: Session = Depends(get_db),
):
    client = queries.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.thesis_json = body.thesis_json
    client.config_json = body.config_json
    db.commit()
    db.refresh(client)
    return ClientResponse.model_validate(client)
