"""Tests for the batch generation endpoint."""

TRANSCRIPT_1 = """Doctor: What brings you in today?
Patient: I've had a cough for about a week. It's productive with yellowish mucus.
Doctor: Any fever?
Patient: Yes, 101.2 last night.
Doctor: I'll examine you. Decreased breath sounds right lower lobe. Likely pneumonia.
Doctor: Starting azithromycin 500mg today then 250mg x4 days. Follow up in 48 hours."""

TRANSCRIPT_2 = """Doctor: Hi, how are you feeling?
Patient: My knee has been hurting for 3 days after I twisted it playing soccer.
Doctor: Any swelling or instability?
Patient: Yes, it swelled up right away. Feels unstable when I pivot.
Doctor: Positive Lachman test. Suspected ACL tear. Getting an MRI today.
Doctor: Ice and elevation. Ibuprofen 600mg TID. Referral to orthopedics."""


def test_batch_generate_multiple_transcripts(client):
    response = client.post(
        "/api/v1/batch-generate",
        json={"transcripts": [TRANSCRIPT_1, TRANSCRIPT_2]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 2
    assert data["succeeded"] == 2
    assert len(data["results"]) == 2


def test_batch_generate_single_transcript(client):
    response = client.post(
        "/api/v1/batch-generate",
        json={"transcripts": [TRANSCRIPT_1]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["succeeded"] >= 0


def test_batch_generate_empty_list_rejected(client):
    response = client.post(
        "/api/v1/batch-generate",
        json={"transcripts": []},
    )
    assert response.status_code == 422


def test_batch_generate_too_many_rejected(client):
    # max is 10
    transcripts = [TRANSCRIPT_1] * 11
    response = client.post(
        "/api/v1/batch-generate",
        json={"transcripts": transcripts},
    )
    assert response.status_code == 422


def test_batch_generate_results_have_soap_structure(client):
    response = client.post(
        "/api/v1/batch-generate",
        json={"transcripts": [TRANSCRIPT_1]},
    )
    assert response.status_code == 200
    data = response.json()
    if data["succeeded"] > 0:
        result = data["results"][0]
        assert "soap_note" in result
        assert "metadata" in result
        soap = result["soap_note"]
        for section in ["subjective", "objective", "assessment", "plan"]:
            assert section in soap


def test_batch_generate_marks_invalid_transcripts_as_failed(client):
    response = client.post(
        "/api/v1/batch-generate",
        json={"transcripts": ["short", TRANSCRIPT_2]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["failed_indices"] == [0]
    assert data["succeeded"] == 1


def test_batch_generate_can_skip_raw_json(client):
    response = client.post(
        "/api/v1/batch-generate",
        json={
            "transcripts": [TRANSCRIPT_1],
            "mode": "demo",
            "include_raw_json": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["raw_json"] is None
