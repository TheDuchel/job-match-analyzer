import json

from fastapi.testclient import TestClient

from job_analyzer.api import app, get_llm
from tests.test_analyzer import FakeLLM, VALID_POSTING

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_rejects_short_input():
    response = client.post("/analyze", json={"posting": "short", "cv": "short"})
    assert response.status_code == 422


def test_analyze_with_fake_llm():
    match_reply = json.dumps({"found_skills": ["Python"], "summary": "Partial fit.", "relevant_years": 1})
    fake = FakeLLM([json.dumps(VALID_POSTING), match_reply])
    app.dependency_overrides[get_llm] = lambda: fake

    try:
        response = client.post("/analyze", json={
            "posting": "A long enough job posting text for validation.",
            "cv": "A long enough CV text for validation purposes.",
        })
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["posting"]["title"] == "Développeur Python"
    assert body["match"]["missing_skills"] == ["SQL", "Docker"]