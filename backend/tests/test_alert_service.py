import uuid
from unittest.mock import MagicMock

import pytest

from models.alert import Alert
from models.client import Client
from models.company import Company
from models.score import Score
from services.alert_service import AlertService


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def fo_client(db):
    c = Client(
        name="Apex Capital",
        thesis_json={},
        config_json={
            "alerts_enabled": True,
            "alert_threshold": 7.5,
            "phone_number": "+15551234567",
            "dashboard_url": "https://app.example.com",
        },
    )
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def company(db, fo_client):
    co = Company(
        client_id=fo_client.id,
        name="Acme AI",
        sector="AI/ML",
        stage="Seed",
        source="github",
        source_url="https://github.com/acme",
        raw_data={},
    )
    db.add(co)
    db.flush()
    return co


@pytest.fixture
def reach_out_score(db, company, fo_client):
    s = Score(
        company_id=company.id,
        client_id=fo_client.id,
        total_score=8.5,
        dimension_scores={"thesis_fit": 9, "team_signals": 8, "market_timing": 8, "data_quality": 9},
        scoring_notes="Strong fit.",
        recommendation="REACH_OUT",
    )
    db.add(s)
    db.flush()
    return s


def _make_service(db, twilio_mock=None):
    return AlertService(db, twilio_client=twilio_mock or MagicMock())


# ── tests ─────────────────────────────────────────────────────────────────────

def test_alert_fires_when_all_conditions_met(db, fo_client, company, reach_out_score):
    mock_twilio = MagicMock()
    service = _make_service(db, mock_twilio)

    result = service.send_deal_alert(fo_client.id, company.id, reach_out_score)

    assert result is True
    mock_twilio.messages.create.assert_called_once()
    call_kwargs = mock_twilio.messages.create.call_args.kwargs
    assert "8.5/10" in call_kwargs["body"]
    assert "REACH_OUT" in call_kwargs["body"]
    assert "Acme AI" in call_kwargs["body"]
    assert "Apex Capital" in call_kwargs["body"]
    assert call_kwargs["to"] == "+15551234567"


def test_alert_logged_to_alerts_table(db, fo_client, company, reach_out_score):
    service = _make_service(db)
    service.send_deal_alert(fo_client.id, company.id, reach_out_score)

    alert = db.query(Alert).filter(Alert.client_id == fo_client.id).first()
    assert alert is not None
    assert alert.channel == "sms"
    assert "8.5/10" in alert.message
    assert alert.company_id == company.id


def test_alert_skipped_when_disabled(db, fo_client, company, reach_out_score):
    fo_client.config_json = {**fo_client.config_json, "alerts_enabled": False}
    db.flush()

    mock_twilio = MagicMock()
    result = _make_service(db, mock_twilio).send_deal_alert(fo_client.id, company.id, reach_out_score)

    assert result is False
    mock_twilio.messages.create.assert_not_called()


def test_alert_skipped_below_threshold(db, fo_client, company, reach_out_score):
    reach_out_score.total_score = 5.0
    db.flush()

    mock_twilio = MagicMock()
    result = _make_service(db, mock_twilio).send_deal_alert(fo_client.id, company.id, reach_out_score)

    assert result is False
    mock_twilio.messages.create.assert_not_called()


def test_alert_skipped_when_not_reach_out(db, fo_client, company, reach_out_score):
    reach_out_score.recommendation = "WATCH"
    db.flush()

    mock_twilio = MagicMock()
    result = _make_service(db, mock_twilio).send_deal_alert(fo_client.id, company.id, reach_out_score)

    assert result is False
    mock_twilio.messages.create.assert_not_called()


def test_alert_skipped_when_no_phone(db, fo_client, company, reach_out_score):
    fo_client.config_json = {**fo_client.config_json, "phone_number": ""}
    db.flush()

    mock_twilio = MagicMock()
    result = _make_service(db, mock_twilio).send_deal_alert(fo_client.id, company.id, reach_out_score)

    assert result is False
    mock_twilio.messages.create.assert_not_called()


def test_alert_includes_deal_url(db, fo_client, company, reach_out_score):
    service = _make_service(db)
    service.send_deal_alert(fo_client.id, company.id, reach_out_score)

    alert = db.query(Alert).filter(Alert.client_id == fo_client.id).first()
    assert f"/deals/{company.id}" in alert.message


def test_alert_skipped_for_unknown_client(db, company, reach_out_score):
    mock_twilio = MagicMock()
    result = _make_service(db, mock_twilio).send_deal_alert(
        uuid.uuid4(), company.id, reach_out_score
    )

    assert result is False
    mock_twilio.messages.create.assert_not_called()
