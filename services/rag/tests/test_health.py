"""Health, readiness, and info endpoint tests."""


def test_info_returns_metadata(client):
    resp = client.get("/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "version" in data
    assert data["environment"] == "development"


def test_health_returns_200(client):
    # The app lifespan is not started in tests, so the database component reports
    # an error and overall status is "degraded" — but the endpoint still answers 200.
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
    assert "rag" in data


def test_ready_reports_503_without_db(client):
    # Readiness must fail closed when the database is unavailable.
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["status"] == "error"
