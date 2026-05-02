"""Tests for the stats endpoint."""

def test_stats_returns_structure(client):
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_notes_saved" in data
    assert "by_generation_mode" in data
    assert "server" in data
    assert isinstance(data["total_notes_saved"], int)
    assert isinstance(data["by_generation_mode"], dict)


def test_stats_server_info(client):
    response = client.get("/api/v1/stats")
    data = response.json()
    server = data["server"]
    assert "version" in server
    assert "generation_mode" in server
    assert "openai_configured" in server
    assert "anthropic_configured" in server
