from unittest.mock import patch

import pytest

from models.client import Client


@pytest.fixture
def fo_client(db):
    c = Client(name="Test FO", thesis_json={}, config_json={})
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def auth_client_id(fo_client):
    return fo_client.id


def test_run_pipeline_queues_task(api_client, fo_client):
    with patch("routers.pipeline_router.run_pipeline_for_client") as mock_task:
        mock_task.delay.return_value.id = "test-job-id"
        resp = api_client.post("/api/pipeline/run")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "queued"
    assert body["job_id"] == "test-job-id"
    mock_task.delay.assert_called_once_with(str(fo_client.id))


def test_run_pipeline_dispatches_authenticated_client(api_client, fo_client):
    """client_id in the dispatch comes from the auth token, not a request body."""
    with patch("routers.pipeline_router.run_pipeline_for_client") as mock_task:
        mock_task.delay.return_value.id = "job-abc"
        api_client.post("/api/pipeline/run")

    mock_task.delay.assert_called_once_with(str(fo_client.id))


def test_pipeline_status_pending(api_client, fo_client):
    with patch("routers.pipeline_router.celery_app") as mock_app:
        mock_app.AsyncResult.return_value.state = "PENDING"
        mock_app.AsyncResult.return_value.result = None
        resp = api_client.get("/api/pipeline/status/some-job-id")

    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == "some-job-id"
    assert body["status"] == "PENDING"
    assert body["result"] is None


def test_pipeline_status_success(api_client, fo_client):
    with patch("routers.pipeline_router.celery_app") as mock_app:
        mock_app.AsyncResult.return_value.state = "SUCCESS"
        mock_app.AsyncResult.return_value.result = {"new_companies": 5, "scraper_errors": []}
        resp = api_client.get("/api/pipeline/status/done-job-id")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["result"]["new_companies"] == 5


def test_pipeline_status_failure(api_client, fo_client):
    with patch("routers.pipeline_router.celery_app") as mock_app:
        mock_app.AsyncResult.return_value.state = "FAILURE"
        mock_app.AsyncResult.return_value.result = None
        resp = api_client.get("/api/pipeline/status/failed-job-id")

    assert resp.status_code == 200
    assert resp.json()["status"] == "FAILURE"
    assert resp.json()["result"] is None
