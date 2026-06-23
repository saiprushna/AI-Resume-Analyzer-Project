"""FastAPI app — upload resume, analyze with AI, return job prep insights."""

import logging
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from analyzer import analyze_resume_text
from config import ALLOWED_RESUME_EXTENSIONS, ROLE_GROUPS, STATIC_DIR, TARGET_ROLES, get_settings
from db import get_latest, init_db, save_analysis
from models import AnalyzeResponse, HealthResponse, RoleGroup, RolesResponse
from resume_parser import extract_text, file_extension

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(
    title="AI Job Assistant",
    description="Upload resume → ATS score, skill gaps, projects, mock interview prep",
    version="1.0.0",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_rate_limit: dict[str, float] = {}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(request: Request):
    settings = get_settings()
    ip = _client_ip(request)
    now = time.time()
    last = _rate_limit.get(ip, 0)
    if now - last < settings.rate_limit_seconds:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Please wait {settings.rate_limit_seconds} seconds and try again.",
        )
    _rate_limit[ip] = now


@app.on_event("startup")
def startup():
    init_db()
    settings = get_settings()
    log.info("AI Job Assistant started (LLM: %s)", settings.llm_provider)


@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(index_path)


@app.get("/api/health", response_model=HealthResponse)
def health():
    settings = get_settings()
    has_key = bool(
        settings.gemini_api_key
        if settings.llm_provider == "gemini"
        else settings.openai_api_key
    )
    return HealthResponse(
        status="ok" if has_key else "degraded",
        llm=settings.llm_provider if has_key else f"{settings.llm_provider} (missing API key)",
    )


@app.get("/api/roles", response_model=RolesResponse)
def roles():
    return RolesResponse(
        roles=TARGET_ROLES,
        groups=[RoleGroup(label=group["label"], roles=group["roles"]) for group in ROLE_GROUPS],
    )


@app.get("/api/recent")
def recent():
    return {"recent": get_latest()}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    target_role: str = Form(...),
):
    _check_rate_limit(request)
    settings = get_settings()

    if target_role not in TARGET_ROLES:
        raise HTTPException(status_code=400, detail="Invalid target role.")

    filename = file.filename or ""
    ext = file_extension(filename)
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or DOCX file only.",
        )

    file_bytes = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File is too large. Maximum size is {settings.max_upload_mb} MB.",
        )

    try:
        resume_text = extract_text(file_bytes, filename=filename)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    try:
        result = analyze_resume_text(resume_text, target_role)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:
        log.exception("Analysis failed")
        raise HTTPException(
            status_code=502,
            detail="AI analysis failed. Please try again in a moment.",
        ) from error

    response_dict = result.model_dump(mode="json")
    save_analysis(response_dict)
    return result
