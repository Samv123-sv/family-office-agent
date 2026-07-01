import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import db.queries as queries
from auth.clerk import get_authenticated_client
from database import get_db
from models.company import Company
from schemas import CompanyDetail, CompanyListItem, PaginatedDeals, ScoreSummary

router = APIRouter(tags=["deals"])

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)


@router.get("/deals", response_model=PaginatedDeals)
def list_deals(
    client_id: UUID = Depends(get_authenticated_client),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sector: str | None = None,
    stage: str | None = None,
    min_score: float | None = None,
    recommendation: str | None = None,
    db: Session = Depends(get_db),
):
    companies = queries.list_companies(db, client_id, sector=sector, stage=stage)

    items: list[tuple[Company, object]] = []
    for company in companies:
        score = queries.latest_score(db, company.id, client_id)
        if min_score is not None and (score is None or score.total_score < min_score):
            continue
        if recommendation and (score is None or score.recommendation != recommendation):
            continue
        items.append((company, score))

    items.sort(key=lambda x: x[1].scored_at if x[1] else _EPOCH, reverse=True)

    total = len(items)
    offset = (page - 1) * limit
    page_items = items[offset : offset + limit]

    return PaginatedDeals(
        items=[
            CompanyListItem(
                **{c: getattr(co, c) for c in ["id", "client_id", "name", "sector", "stage", "source", "source_url", "created_at"]},
                score=ScoreSummary.model_validate(sc) if sc else None,
            )
            for co, sc in page_items
        ],
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
    )


@router.get("/deals/{company_id}", response_model=CompanyDetail)
def get_deal(
    company_id: UUID,
    client_id: UUID = Depends(get_authenticated_client),
    db: Session = Depends(get_db),
):
    # Existence check first, then ownership — returns 404 vs 403 correctly
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company.client_id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")

    score = queries.latest_score(db, company_id, client_id)
    memo = queries.latest_memo(db, company_id, client_id)

    return CompanyDetail(
        **{c: getattr(company, c) for c in [
            "id", "client_id", "name", "sector", "stage",
            "funding_total", "latest_round_size", "source", "source_url",
            "raw_data", "created_at",
        ]},
        score={
            "score_id": str(score.id),
            "total_score": score.total_score,
            "recommendation": score.recommendation,
            "dimension_scores": score.dimension_scores,
            "scoring_notes": score.scoring_notes,
            "scored_at": score.scored_at.isoformat(),
        } if score else None,
        memo={
            "memo_id": str(memo.id),
            "content": memo.content,
            "version": memo.version,
            "generated_at": memo.generated_at.isoformat(),
        } if memo else None,
    )
