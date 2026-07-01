import logging
import uuid

from celery_app import celery_app
from database import SessionLocal
from models.client import Client
from services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def run_pipeline_for_client(self, client_id: str) -> dict:
    """Run the full scrape-score-memo pipeline for a single client."""
    db = SessionLocal()
    try:
        service = PipelineService(db)
        return service.run_full_pipeline(uuid.UUID(client_id))
    except Exception as exc:
        logger.error("pipeline failed client=%s: %s", client_id, exc)
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task
def run_pipeline_for_all_clients() -> dict:
    """Fan out pipeline tasks for every active client. Triggered by Celery beat at 6am UTC."""
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        dispatched = [str(c.id) for c in clients]
        for client_id in dispatched:
            run_pipeline_for_client.delay(client_id)
        logger.info("dispatched pipeline for %d clients", len(dispatched))
        return {"dispatched": len(dispatched), "client_ids": dispatched}
    finally:
        db.close()
