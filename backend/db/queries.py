"""
Centralised query functions. Every function that reads client data requires client_id
and includes it in every WHERE clause — no exceptions.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from models.alert import Alert
from models.client import Client
from models.company import Company
from models.document import Document
from models.memo import Memo
from models.score import Score


def get_client(db: Session, client_id: UUID) -> Client | None:
    return db.query(Client).filter(Client.id == client_id).first()


def get_client_by_org_id(db: Session, clerk_org_id: str) -> Client | None:
    return db.query(Client).filter(Client.clerk_org_id == clerk_org_id).first()


def list_companies(
    db: Session,
    client_id: UUID,
    sector: str | None = None,
    stage: str | None = None,
) -> list[Company]:
    q = db.query(Company).filter(Company.client_id == client_id)
    if sector:
        q = q.filter(Company.sector == sector)
    if stage:
        q = q.filter(Company.stage == stage)
    return q.all()


def get_company(db: Session, company_id: UUID, client_id: UUID) -> Company | None:
    return (
        db.query(Company)
        .filter(Company.id == company_id, Company.client_id == client_id)
        .first()
    )


def latest_score(db: Session, company_id: UUID, client_id: UUID) -> Score | None:
    return (
        db.query(Score)
        .filter(Score.company_id == company_id, Score.client_id == client_id)
        .order_by(Score.scored_at.desc())
        .first()
    )


def latest_memo(db: Session, company_id: UUID, client_id: UUID) -> Memo | None:
    return (
        db.query(Memo)
        .filter(Memo.company_id == company_id, Memo.client_id == client_id)
        .order_by(Memo.generated_at.desc())
        .first()
    )


def list_documents_for_company(
    db: Session, company_id: UUID, client_id: UUID
) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.company_id == company_id, Document.client_id == client_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


def list_alerts(db: Session, client_id: UUID, limit: int = 20) -> list[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.client_id == client_id)
        .order_by(Alert.sent_at.desc())
        .limit(limit)
        .all()
    )
