"""Project settings from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "analyses.db"

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}

TOP_ROLES = [
    "Software Engineer (SDE)",
    "Python Developer",
    "Java Developer",
    "Full Stack Developer",
    "Frontend Developer (React)",
    "Backend Developer",
    "Data Analyst",
    "AI/ML Engineer",
]

MORE_ROLES = [
    "Data Engineer",
    "DevOps Engineer",
    "Cloud Engineer (AWS/GCP)",
    "Node.js Developer",
    "Mobile Developer (Android)",
    "QA Automation Engineer",
    "Cybersecurity Analyst",
    "Business Analyst",
    "Database Administrator",
    "UI/UX Designer",
    "Product Analyst",
    "Technical Support Engineer",
]

TARGET_ROLES = TOP_ROLES + MORE_ROLES

ROLE_GROUPS = [
    {"label": "Top roles", "roles": TOP_ROLES},
    {"label": "More roles", "roles": MORE_ROLES},
]


class Settings:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.model = os.getenv("MODEL", "gemini-2.0-flash")
        self.max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "5"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.rate_limit_seconds = int(os.getenv("RATE_LIMIT_SECONDS", "60"))
        self.port = int(os.getenv("PORT", "8000"))


def get_settings() -> Settings:
    load_dotenv(override=True)
    return Settings()
