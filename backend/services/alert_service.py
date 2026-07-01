import logging
from uuid import UUID

from sqlalchemy.orm import Session

from config import settings
from models.alert import Alert
from models.client import Client
from models.company import Company
from models.score import Score

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLD = 7.5


class AlertService:
    def __init__(self, db: Session, twilio_client=None):
        self.db = db
        self._twilio = twilio_client

    def _get_twilio(self):
        if self._twilio is None:
            from twilio.rest import Client as TwilioClient
            self._twilio = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return self._twilio

    def send_deal_alert(self, client_id: UUID, company_id: UUID, score: Score) -> bool:
        """
        Sends an SMS alert when a deal meets the client's threshold.
        Returns True if the alert was sent, False if skipped.
        Skips silently — never raises.
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False

        config = client.config_json or {}

        if not config.get("alerts_enabled", False):
            return False

        if score.recommendation != "REACH_OUT":
            return False

        threshold = float(config.get("alert_threshold", _DEFAULT_THRESHOLD))
        if score.total_score < threshold:
            return False

        phone = config.get("phone_number", "").strip()
        if not phone:
            return False

        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False

        dashboard_url = config.get("dashboard_url", "https://app.example.com").rstrip("/")
        message = (
            f"New deal alert [{client.name}]: {company.name} scored "
            f"{score.total_score:.1f}/10. {score.recommendation}. "
            f"View: {dashboard_url}/deals/{company_id}"
        )

        self._get_twilio().messages.create(
            body=message,
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone,
        )

        self.db.add(Alert(
            client_id=client_id,
            company_id=company_id,
            channel="sms",
            message=message,
        ))
        self.db.commit()

        logger.info("alert sent client=%s company=%s score=%.1f", client_id, company_id, score.total_score)
        return True
