"""Pydantic models for API requests and LLM responses."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProjectSuggestion(BaseModel):
    title: str
    why: str
    stack: list[str]
    difficulty: str


class InterviewQA(BaseModel):
    question: str
    sample_answer: str
    explanation: str


class ResumeAnalysisResult(BaseModel):
    candidate_name: str | None = None
    target_role: str
    ats_score: int = Field(ge=0, le=100)
    ats_feedback: str
    skills_found: list[str]
    skill_gaps: list[str]
    strengths: list[str]


class InterviewPrepResult(BaseModel):
    project_suggestions: list[ProjectSuggestion]
    mock_interview: list[InterviewQA]

    @field_validator("mock_interview")
    @classmethod
    def require_at_least_ten_questions(cls, value: list[InterviewQA]) -> list[InterviewQA]:
        if len(value) < 10:
            raise ValueError(f"Expected at least 10 mock interview questions, got {len(value)}")
        return value


class AnalyzeResponse(ResumeAnalysisResult):
    project_suggestions: list[ProjectSuggestion]
    mock_interview: list[InterviewQA]
    analyzed_at: datetime


class HealthResponse(BaseModel):
    status: str
    llm: str


class RoleGroup(BaseModel):
    label: str
    roles: list[str]


class RolesResponse(BaseModel):
    roles: list[str]
    groups: list[RoleGroup]
