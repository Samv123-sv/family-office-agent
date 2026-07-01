import logging
import uuid

from celery_app import celery_app
from database import SessionLocal
from services.memo_service import MemoService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_memo(self, company_id: str, client_id: str) -> dict:
    """Generate (or return cached) investment memo for a single company."""
    db = SessionLocal()
    try:
        service = MemoService(db)
        return service.generate_memo(uuid.UUID(company_id), uuid.UUID(client_id))
    except Exception as exc:
        logger.error("memo generation failed company=%s client=%s: %s", company_id, client_id, exc)
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
    finally:
        db.close()
