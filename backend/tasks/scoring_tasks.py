import logging
import uuid

from celery_app import celery_app
from database import SessionLocal
from services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def score_company(self, company_id: str, client_id: str) -> dict:
    """Score a single company against its client's thesis using Claude."""
    db = SessionLocal()
    try:
        service = ScoringService(db)
        result = service.score_company(uuid.UUID(company_id), uuid.UUID(client_id))

        try:
            from models.score import Score
            from services.alert_service import AlertService
            score = (
                db.query(Score)
                .filter(
                    Score.company_id == uuid.UUID(company_id),
                    Score.client_id == uuid.UUID(client_id),
                )
                .order_by(Score.scored_at.desc())
                .first()
            )
            if score:
                AlertService(db).send_deal_alert(
                    uuid.UUID(client_id), uuid.UUID(company_id), score
                )
        except Exception as alert_exc:
            logger.warning("alert failed company=%s: %s", company_id, alert_exc)

        return result
    except Exception as exc:
        logger.error("scoring failed company=%s client=%s: %s", company_id, client_id, exc)
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
    finally:
        db.close()
