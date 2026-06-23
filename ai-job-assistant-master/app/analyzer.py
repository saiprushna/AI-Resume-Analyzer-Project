"""Orchestrate resume analysis — two LLM calls merged into one response."""

import logging
from datetime import datetime, timezone

from llm.client import complete_json
from llm.prompts import (
    INTERVIEW_PREP_SYSTEM,
    INTERVIEW_PREP_USER,
    RESUME_ANALYSIS_SYSTEM,
    RESUME_ANALYSIS_USER,
)
from models import AnalyzeResponse, InterviewPrepResult, ResumeAnalysisResult

log = logging.getLogger(__name__)


def analyze_resume_text(resume_text: str, target_role: str) -> AnalyzeResponse:
    """Run ATS analysis + interview prep and return the full API response."""
    log.info("Analyzing resume for role: %s", target_role)

    analysis_data = complete_json(
        RESUME_ANALYSIS_SYSTEM,
        RESUME_ANALYSIS_USER.format(
            target_role=target_role,
            resume_text=resume_text[:12000],
        ),
    )
    analysis = ResumeAnalysisResult.model_validate(analysis_data)

    prep_data = complete_json(
        INTERVIEW_PREP_SYSTEM,
        INTERVIEW_PREP_USER.format(
            target_role=target_role,
            ats_score=analysis.ats_score,
            skills_found=", ".join(analysis.skills_found),
            skill_gaps=", ".join(analysis.skill_gaps),
            strengths=", ".join(analysis.strengths),
        ),
    )
    prep = InterviewPrepResult.model_validate(prep_data)

    return AnalyzeResponse(
        **analysis.model_dump(),
        project_suggestions=prep.project_suggestions,
        mock_interview=prep.mock_interview,
        analyzed_at=datetime.now(timezone.utc),
    )
