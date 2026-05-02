"""Tests for the evaluation endpoint."""

GENERATED_NOTE = {
    "subjective": "Patient reports 3-day headache, rated 7/10, with nausea.",
    "objective": "BP 132/84, HR 76, Temp 98.8F. Mild neck stiffness.",
    "assessment": "Headache with meningismus. Rule out bacterial meningitis.",
    "plan": "CT head. LP if CT normal. Sumatriptan 100mg PRN. Ondansetron 4mg PRN nausea.",
}

REFERENCE_NOTE = {
    "subjective": "Patient with severe headache for 3 days, 7/10 pain, nausea present.",
    "objective": "BP 132/84, HR 76, T 98.8F. Neck stiffness noted on examination.",
    "assessment": "Headache with meningismus — bacterial meningitis must be ruled out.",
    "plan": "Stat CT head. Lumbar puncture if CT negative. Sumatriptan for pain. Antiemetic as needed.",
}

TRANSCRIPT = """Doctor: What brings you in today?
Patient: Severe headache for 3 days. It's a 7 out of 10. I also feel nauseous.
Doctor: Any fever, neck stiffness?
Patient: My neck feels a bit stiff.
Doctor: Vitals: BP 132/84, HR 76, Temp 98.8. I'm concerned about meningitis.
Doctor: I'll order a CT and LP. Prescribing sumatriptan and ondansetron."""


def test_evaluate_without_reference(client):
    response = client.post(
        "/api/v1/evaluate",
        json={
            "transcript": TRANSCRIPT,
            "generated_note": GENERATED_NOTE,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "scores" in data
    assert "summary" in data
    assert isinstance(data["summary"], str)
    assert len(data["summary"]) > 0


def test_evaluate_with_reference(client):
    response = client.post(
        "/api/v1/evaluate",
        json={
            "transcript": TRANSCRIPT,
            "generated_note": GENERATED_NOTE,
            "reference_note": REFERENCE_NOTE,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    scores = data["scores"]
    assert "summary" in data


def test_evaluate_heuristic_score_range(client):
    """Heuristic score should be between 0 and 1."""
    response = client.post(
        "/api/v1/evaluate",
        json={
            "transcript": TRANSCRIPT,
            "generated_note": GENERATED_NOTE,
        },
    )
    assert response.status_code == 200
    data = response.json()
    section_scores = data["scores"].get("section_scores") or {}
    heuristic = section_scores.get("heuristic_completeness")
    if heuristic is not None:
        assert 0.0 <= heuristic <= 1.0


def test_evaluate_empty_note(client):
    """Evaluation should handle sparse notes gracefully."""
    sparse_note = {
        "subjective": "Unknown",
        "objective": "Not documented.",
        "assessment": "TBD",
        "plan": "N/A",
    }
    response = client.post(
        "/api/v1/evaluate",
        json={
            "transcript": TRANSCRIPT,
            "generated_note": sparse_note,
        },
    )
    assert response.status_code == 200
