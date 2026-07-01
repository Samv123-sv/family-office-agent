from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ── pipeline ──────────────────────────────────────────────────────────────────

class PipelineJobResponse(BaseModel):
    job_id: str
    status: str

class TaskStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None


# ── deals ─────────────────────────────────────────────────────────────────────

class ScoreSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_score: float
    recommendation: Optional[str]
    dimension_scores: dict
    scored_at: datetime

class CompanyListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    client_id: UUID
    name: str
    sector: str
    stage: str
    source: str
    source_url: str
    created_at: datetime
    score: Optional[ScoreSummary]

class PaginatedDeals(BaseModel):
    items: list[CompanyListItem]
    total: int
    page: int
    limit: int
    pages: int

class CompanyDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    client_id: UUID
    name: str
    sector: str
    stage: str
    funding_total: Optional[float]
    latest_round_size: Optional[float]
    source: str
    source_url: str
    raw_data: dict
    created_at: datetime
    score: Optional[dict]
    memo: Optional[dict]


# ── memos ─────────────────────────────────────────────────────────────────────

class MemoResponse(BaseModel):
    memo_id: str
    company_id: str
    client_id: str
    content: str
    version: int
    generated_at: str
    cached: bool


# ── thesis ────────────────────────────────────────────────────────────────────

class ThesisUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thesis_json: dict
    config_json: dict

class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    thesis_json: dict
    config_json: dict
    created_at: datetime


# ── documents ─────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    client_id: UUID
    company_id: Optional[UUID]
    filename: str
    file_type: str
    uploaded_at: datetime


# ── alerts ────────────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    client_id: UUID
    company_id: UUID
    channel: str
    message: str
    sent_at: datetime


# ── health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str
