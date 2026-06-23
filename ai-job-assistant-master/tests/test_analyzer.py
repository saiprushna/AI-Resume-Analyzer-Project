from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from analyzer import analyze_resume_text
from llm.client import complete_json
from llm.prompts import INTERVIEW_PREP_SYSTEM, INTERVIEW_PREP_USER, RESUME_ANALYSIS_SYSTEM, RESUME_ANALYSIS_USER
from models import AnalyzeResponse, InterviewPrepResult, ResumeAnalysisResult


SAMPLE_RESUME = """
Ravi Kumar
Python Developer | Hyderabad
Skills: Python, SQL, Flask, Git
Projects: Attendance Tracker with Flask, Weather Dashboard
Education: B.Tech CSE, JNTU Hyderabad, CGPA 8.1
"""

MOCK_INTERVIEW = [
    {
        "question": f"Interview question {index}?",
        "sample_answer": "This is a detailed sample answer with enough context for the candidate to learn from.",
        "explanation": "This is a detailed explanation covering why the question is asked, key concepts, and common mistakes.",
    }
    for index in range(1, 11)
]

ANALYSIS_JSON = {
    "candidate_name": "Ravi Kumar",
    "target_role": "Python Developer",
    "ats_score": 62,
    "ats_feedback": "Good Python skills and relevant projects, but add metrics and Docker experience.",
    "skills_found": ["Python", "Flask"],
    "skill_gaps": ["Docker"],
    "strengths": ["Projects"],
}

PREP_JSON = {
    "project_suggestions": [
        {
            "title": "Dockerized Flask App",
            "why": "This project helps you practice containerization and deployment.",
            "stack": ["Python", "Docker"],
            "difficulty": "intermediate",
        },
        {
            "title": "CI Pipeline",
            "why": "Shows you understand automated testing and delivery.",
            "stack": ["GitHub Actions"],
            "difficulty": "intermediate",
        },
        {
            "title": "API Testing Suite",
            "why": "Demonstrates quality engineering skills interviewers value.",
            "stack": ["pytest"],
            "difficulty": "beginner",
        },
    ],
    "mock_interview": MOCK_INTERVIEW,
}


def test_resume_analysis_model_validation():
    result = ResumeAnalysisResult.model_validate(ANALYSIS_JSON)
    assert result.ats_score == 62


def test_interview_prep_requires_three_projects_and_ten_questions():
    prep = InterviewPrepResult.model_validate(PREP_JSON)
    assert len(prep.project_suggestions) == 3
    assert len(prep.mock_interview) == 10


def test_interview_prep_rejects_fewer_than_ten_questions():
    bad_prep = {
        **PREP_JSON,
        "mock_interview": MOCK_INTERVIEW[:5],
    }
    with pytest.raises(ValueError):
        InterviewPrepResult.model_validate(bad_prep)


def test_analyze_resume_text_merges_calls():
    with patch("analyzer.complete_json", side_effect=[ANALYSIS_JSON, PREP_JSON]):
        result = analyze_resume_text(SAMPLE_RESUME, "Python Developer")
    assert isinstance(result, AnalyzeResponse)
    assert result.candidate_name == "Ravi Kumar"
    assert len(result.project_suggestions) == 3
    assert len(result.mock_interview) == 10
    assert result.analyzed_at <= datetime.now(timezone.utc)


def test_complete_json_falls_back_when_gemini_is_quota_limited():
    with patch("llm.client.get_settings", return_value=SimpleNamespace(llm_provider="gemini")):
        with patch(
            "llm.client._call_gemini",
            side_effect=RuntimeError("Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests"),
        ):
            analysis = complete_json(
                RESUME_ANALYSIS_SYSTEM,
                RESUME_ANALYSIS_USER.format(target_role="Python Developer", resume_text=SAMPLE_RESUME.strip()),
            )

    assert analysis["target_role"] == "Python Developer"
    assert 20 <= analysis["ats_score"] <= 100
    assert analysis["skills_found"]

    with patch("llm.client.get_settings", return_value=SimpleNamespace(llm_provider="gemini")):
        with patch(
            "llm.client._call_gemini",
            side_effect=RuntimeError("Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests"),
        ):
            prep = complete_json(
                INTERVIEW_PREP_SYSTEM,
                INTERVIEW_PREP_USER.format(
                    target_role="Python Developer",
                    ats_score=analysis["ats_score"],
                    skills_found=", ".join(analysis["skills_found"]),
                    skill_gaps=", ".join(analysis["skill_gaps"]),
                    strengths=", ".join(analysis["strengths"]),
                ),
            )

    assert len(prep["project_suggestions"]) == 3
    assert len(prep["mock_interview"]) == 10


def test_analyze_response_schema():
    data = {**ANALYSIS_JSON, **PREP_JSON, "analyzed_at": datetime.now(timezone.utc)}
    response = AnalyzeResponse.model_validate(data)
    assert response.target_role == "Python Developer"
