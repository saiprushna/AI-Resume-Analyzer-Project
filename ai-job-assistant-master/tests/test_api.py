from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from models import AnalyzeResponse

client = TestClient(app)


def _mock_interview():
    return [
        {
            "question": f"Question {index}?",
            "sample_answer": "Detailed sample answer for interview preparation.",
            "explanation": "Detailed explanation of concepts, evaluation criteria, and common mistakes.",
        }
        for index in range(1, 11)
    ]


def _mock_result(target_role="Python Developer", score=65):
    return {
        "candidate_name": "Ravi Kumar",
        "target_role": target_role,
        "ats_score": score,
        "ats_feedback": "Detailed feedback about resume strengths and improvement areas.",
        "skills_found": ["Python"],
        "skill_gaps": ["Docker"],
        "strengths": ["Projects"],
        "project_suggestions": [
            {
                "title": "P1",
                "why": "Detailed reason this project helps close skill gaps.",
                "stack": ["Python"],
                "difficulty": "beginner",
            }
        ] * 3,
        "mock_interview": _mock_interview(),
        "analyzed_at": "2026-06-21T10:00:00+00:00",
    }


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "llm" in body


def test_roles_endpoint():
    response = client.get("/api/roles")
    assert response.status_code == 200
    body = response.json()
    roles = body["roles"]
    assert "Python Developer" in roles
    assert "Software Engineer (SDE)" in roles
    assert len(roles) >= 15
    assert len(body["groups"]) == 2
    assert body["groups"][0]["label"] == "Top roles"


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200


def test_analyze_rejects_unsupported_format():
    response = client.post(
        "/api/analyze",
        data={"target_role": "Python Developer"},
        files={"file": ("resume.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_analyze_with_mocked_pipeline(sample_pdf_bytes):
    with patch(
        "main.analyze_resume_text",
        return_value=AnalyzeResponse.model_validate(_mock_result()),
    ):
        response = client.post(
            "/api/analyze",
            data={"target_role": "Python Developer"},
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["ats_score"] == 65
    assert body["candidate_name"] == "Ravi Kumar"
    assert len(body["mock_interview"]) == 10


def test_analyze_accepts_docx_with_mocked_pipeline(sample_docx_bytes):
    with patch(
        "main.analyze_resume_text",
        return_value=AnalyzeResponse.model_validate(_mock_result("Java Developer", 68)),
    ):
        response = client.post(
            "/api/analyze",
            data={"target_role": "Java Developer"},
            files={
                "file": (
                    "resume.docx",
                    sample_docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["target_role"] == "Java Developer"
    assert len(body["mock_interview"]) == 10
