from unittest.mock import patch, MagicMock


def test_health_all_ok(api_client):
    with patch("routers.health_router.redis") as mock_redis:
        mock_redis.from_url.return_value.ping.return_value = True
        resp = api_client.get("/api/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["redis"] == "ok"


def test_health_redis_unavailable(api_client):
    with patch("routers.health_router.redis") as mock_redis:
        mock_redis.from_url.return_value.ping.side_effect = ConnectionError("no redis")
        resp = api_client.get("/api/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["redis"] == "unavailable"
    assert body["db"] == "ok"
    assert body["status"] == "degraded"


def test_health_db_always_ok_with_sqlite(api_client):
    """DB check passes because the test client uses SQLite in-memory."""
    with patch("routers.health_router.redis") as mock_redis:
        mock_redis.from_url.return_value.ping.return_value = True
        resp = api_client.get("/api/health")

    assert resp.json()["db"] == "ok"
