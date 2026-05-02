"""Tests for the demo transcript endpoints."""

EXPECTED_DEMO_COUNT = 8


def test_demo_list_has_correct_count(client):
    response = client.get("/api/v1/demo-transcripts/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == EXPECTED_DEMO_COUNT


def test_demo_list_items_have_required_fields(client):
    response = client.get("/api/v1/demo-transcripts/list")
    data = response.json()
    for item in data:
        assert "index" in item
        assert "title" in item
        assert "description" in item
        assert isinstance(item["index"], int)


def test_get_all_demo_transcripts(client):
    for i in range(EXPECTED_DEMO_COUNT):
        response = client.get(f"/api/v1/demo-transcript?index={i}")
        assert response.status_code == 200, f"Demo index {i} failed"
        data = response.json()
        assert "transcript" in data
        assert "title" in data
        assert "expected_chief_complaint" in data
        assert len(data["transcript"]) >= 100, f"Demo {i} transcript too short"


def test_demo_index_out_of_range(client):
    response = client.get("/api/v1/demo-transcript?index=99")
    assert response.status_code == 422


def test_demo_index_negative(client):
    response = client.get("/api/v1/demo-transcript?index=-1")
    assert response.status_code == 422


def test_demo_mental_health_transcript(client):
    """Mental health demo should be available."""
    response = client.get("/api/v1/demo-transcript?index=3")
    assert response.status_code == 200
    data = response.json()
    assert "mental" in data["title"].lower() or "health" in data["title"].lower() or "depression" in data["expected_chief_complaint"].lower()


def test_demo_emergency_transcript(client):
    """Emergency chest pain demo should be available."""
    response = client.get("/api/v1/demo-transcript?index=4")
    assert response.status_code == 200
    data = response.json()
    assert "chest" in data["expected_chief_complaint"].lower() or "emergency" in data["title"].lower()
