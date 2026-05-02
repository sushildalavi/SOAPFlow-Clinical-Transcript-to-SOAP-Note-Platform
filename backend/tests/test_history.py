"""Tests for the history CRUD endpoints."""
SAMPLE_SOAP = {
    "subjective": "Patient reports headache x3 days, 7/10 pain.",
    "objective": "BP 132/84, HR 76, Temp 98.8F. Mild neck stiffness on exam.",
    "assessment": "Headache with meningismus — rule out meningitis.",
    "plan": "CT head, LP if CT normal. Sumatriptan, ondansetron.",
}

SAMPLE_METADATA = {
    "model": "demo-rule-based",
    "mode": "demo",
    "processing_time_ms": 12.3,
    "transcript_word_count": 150,
    "note_word_count": 50,
    "sections_populated": 4,
}


def test_save_note_returns_201(client):
    response = client.post(
        "/api/v1/history",
        json={
            "transcript": "Doctor: What brings you in?\nPatient: Headache for 3 days.",
            "soap_note": SAMPLE_SOAP,
            "metadata": SAMPLE_METADATA,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["id"] > 0
    assert data["soap_note"]["subjective"] == SAMPLE_SOAP["subjective"]


def test_save_note_auto_generates_title(client):
    response = client.post(
        "/api/v1/history",
        json={
            "transcript": "Doctor: Hi\nPatient: I have chest pain.",
            "soap_note": SAMPLE_SOAP,
            "metadata": SAMPLE_METADATA,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"]  # should not be empty


def test_save_note_with_custom_title(client):
    response = client.post(
        "/api/v1/history",
        json={
            "transcript": "Doctor: Hi\nPatient: Knee pain.",
            "soap_note": SAMPLE_SOAP,
            "metadata": SAMPLE_METADATA,
            "title": "My Custom Note",
        },
    )
    assert response.status_code == 201
    assert response.json()["title"] == "My Custom Note"


def test_list_notes_returns_notes(client):
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert "notes" in data
    assert "total" in data
    assert isinstance(data["notes"], list)
    assert data["total"] >= 0


def test_list_notes_pagination(client):
    response = client.get("/api/v1/history?limit=1&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["notes"]) <= 1


def test_get_note_by_id(client):
    # First save a note
    save_resp = client.post(
        "/api/v1/history",
        json={
            "transcript": "Doctor: Any pain?\nPatient: Back pain for a week.",
            "soap_note": SAMPLE_SOAP,
            "metadata": SAMPLE_METADATA,
        },
    )
    note_id = save_resp.json()["id"]

    # Then retrieve it
    get_resp = client.get(f"/api/v1/history/{note_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == note_id


def test_get_nonexistent_note_returns_404(client):
    response = client.get("/api/v1/history/99999")
    assert response.status_code == 404


def test_delete_note(client):
    # Save a note first
    save_resp = client.post(
        "/api/v1/history",
        json={
            "transcript": "Doctor: Hi\nPatient: Fever.",
            "soap_note": SAMPLE_SOAP,
            "metadata": SAMPLE_METADATA,
        },
    )
    note_id = save_resp.json()["id"]

    # Delete it
    del_resp = client.delete(f"/api/v1/history/{note_id}")
    assert del_resp.status_code == 204

    # Verify gone
    get_resp = client.get(f"/api/v1/history/{note_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_note_returns_404(client):
    response = client.delete("/api/v1/history/99999")
    assert response.status_code == 404


def test_clear_all_history(client):
    # First save some notes
    for i in range(3):
        client.post(
            "/api/v1/history",
            json={
                "transcript": f"Doctor: Hi\nPatient: Issue {i}.",
                "soap_note": SAMPLE_SOAP,
                "metadata": SAMPLE_METADATA,
            },
        )
    # Clear all
    response = client.delete("/api/v1/history")
    assert response.status_code == 204
