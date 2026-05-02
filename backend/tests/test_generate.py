"""Tests for the SOAP generation endpoint."""

SAMPLE_TRANSCRIPT = """
Doctor: What brings you in today?
Patient: I've had a severe headache for the past 3 days. It's about a 7 out of 10 in severity.
Doctor: Is it constant or does it come and go?
Patient: It's mostly constant. I also feel nauseous.
Doctor: Any fever, vision changes, or neck stiffness?
Patient: No fever, no vision changes. My neck is a bit stiff.
Doctor: Let me examine you. Your blood pressure is 132 over 84, heart rate 76, temperature 98.8, respiratory rate 16.
Patient: Is anything serious going on?
Doctor: I want to rule out meningitis given the neck stiffness. I'll order a CT scan and lumbar puncture if the CT is normal. In the meantime, I'm prescribing sumatriptan for the pain and ondansetron for nausea.
Patient: Okay, thank you doctor.
"""


def test_generate_returns_valid_soap(client):
    response = client.post(
        "/api/v1/generate",
        json={"transcript": SAMPLE_TRANSCRIPT, "mode": "demo"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    soap = data["soap_note"]
    assert "subjective" in soap
    assert "objective" in soap
    assert "assessment" in soap
    assert "plan" in soap
    # All sections should have some content
    for section in ["subjective", "objective", "assessment", "plan"]:
        assert isinstance(soap[section], str)
        assert len(soap[section]) > 0


def test_generate_includes_metadata(client):
    response = client.post(
        "/api/v1/generate",
        json={"transcript": SAMPLE_TRANSCRIPT, "mode": "demo"},
    )
    assert response.status_code == 200
    data = response.json()
    meta = data["metadata"]
    assert meta["transcript_word_count"] > 0
    assert meta["transcript_char_count"] > 0
    assert meta["processing_time_ms"] >= 0
    assert meta["mode"] in ["demo", "openai", "anthropic"]


def test_generate_includes_raw_json(client):
    response = client.post(
        "/api/v1/generate",
        json={"transcript": SAMPLE_TRANSCRIPT, "mode": "demo", "include_raw_json": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["raw_json"] is not None
    assert "subjective" in data["raw_json"]


def test_generate_rejects_too_short_transcript(client):
    response = client.post(
        "/api/v1/generate",
        json={"transcript": "short", "mode": "demo"},
    )
    assert response.status_code in [400, 422]


def test_generate_rejects_invalid_mode(client):
    response = client.post(
        "/api/v1/generate",
        json={"transcript": SAMPLE_TRANSCRIPT, "mode": "invalid-mode"},
    )
    assert response.status_code == 422


def test_generate_warnings_structure(client):
    response = client.post(
        "/api/v1/generate",
        json={"transcript": SAMPLE_TRANSCRIPT, "mode": "demo"},
    )
    assert response.status_code == 200
    data = response.json()
    warnings = data["warnings"]
    assert isinstance(warnings, list)
    for w in warnings:
        assert "code" in w
        assert "message" in w
        assert "severity" in w
