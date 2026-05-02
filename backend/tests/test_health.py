"""Tests for the health endpoint."""


def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "generation_mode" in data
    assert "openai_configured" in data
    assert "anthropic_configured" in data


def test_root_returns_app_info(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SOAPFlow"
    assert data["status"] == "running"


def test_demo_transcript_endpoint(client):
    response = client.get("/api/v1/demo-transcript?index=0")
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert "title" in data
    assert len(data["transcript"]) > 100


def test_demo_transcript_list(client):
    response = client.get("/api/v1/demo-transcripts/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 8
    for item in data:
        assert "index" in item
        assert "title" in item
