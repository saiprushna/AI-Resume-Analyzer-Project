import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
sys.path.insert(0, str(APP))


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("RATE_LIMIT_SECONDS", "0")
    monkeypatch.setenv("MAX_UPLOAD_MB", "5")
    monkeypatch.setattr("config.load_dotenv", lambda *args, **kwargs: False)


SAMPLE_PDF = ROOT / "data" / "sample_resumes" / "sample_btech_resume.pdf"
SAMPLE_DOCX = ROOT / "data" / "sample_resumes" / "sample_btech_resume.docx"


def _ensure_sample_files():
    if SAMPLE_PDF.exists() and SAMPLE_DOCX.exists():
        return
    import subprocess
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_sample_resume.py")],
        check=True,
    )


@pytest.fixture(scope="session")
def sample_pdf_bytes():
    _ensure_sample_files()
    return SAMPLE_PDF.read_bytes()


@pytest.fixture(scope="session")
def sample_docx_bytes():
    _ensure_sample_files()
    return SAMPLE_DOCX.read_bytes()
