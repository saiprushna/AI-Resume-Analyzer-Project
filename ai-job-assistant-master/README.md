# AI Job Assistant

Upload a resume (PDF or DOCX) and get **ATS score**, **skill gap analysis**, **3 portfolio project ideas**, and **10 mock interview Q&As** with detailed explanations — built for students and junior developers.

**Author:** [K HUNNURJI RAO](https://github.com/hunnurjirao) · [Portfolio](https://hunnurjirao.netlify.app)

## Features

- Resume upload — **PDF or DOCX** (max 5 MB)
- **20 target roles** — grouped as Top roles + More roles
- ATS score (0–100) with detailed feedback
- Skills found vs skill gaps for your target role
- 3 tailored portfolio project suggestions
- **10 mock interview questions** with sample answers and detailed explanations
- SQLite audit trail of past analyses
- Deploy-ready Docker image for Render

## Stack

Python 3.11 · FastAPI · pdfplumber · python-docx · Gemini (or OpenAI)

## Quick start

```bash
git clone https://github.com/hunnurjirao/ai-job-assistant.git
cd ai-job-assistant
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY from https://aistudio.google.com/apikey

python scripts/generate_sample_resume.py
chmod +x run.sh
./run.sh --reload
# Open http://localhost:8000
```

Upload `data/sample_resumes/sample_btech_resume.pdf` or `.docx` to test.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI |
| GET | `/api/health` | Health check |
| GET | `/api/roles` | Target job roles |
| POST | `/api/analyze` | Upload resume + `target_role` form field |

## Project layout

```
ai-job-assistant/
├── app/
│   ├── main.py              # FastAPI routes
│   ├── resume_parser.py     # PDF/DOCX → text
│   ├── analyzer.py          # Two LLM calls
│   ├── llm/                 # Prompts + Gemini/OpenAI client
│   ├── db.py                # SQLite storage
│   └── static/              # Upload UI
├── data/sample_resumes/     # Demo PDF + DOCX
├── tests/
├── scripts/
├── Dockerfile
└── run.sh
```

## Deploy to Render

1. Push this repo to [GitHub](https://github.com/hunnurjirao)
2. Create Render Web Service → Docker
3. Add environment variable: `GEMINI_API_KEY`
4. Deploy → share live URL in your portfolio

Local Docker test:

```bash
./scripts/deploy-render.sh
docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY ai-job-assistant
```

## Tests

```bash
python scripts/generate_sample_resume.py
pytest tests/ -v
```

## Environment variables

```bash
GEMINI_API_KEY=your-key          # required (or use OpenAI)
LLM_PROVIDER=gemini              # gemini | openai
MODEL=gemini-2.0-flash
MAX_UPLOAD_MB=5
RATE_LIMIT_SECONDS=60
PORT=8000
```

## License

MIT — free to use, fork, and learn from. Star the repo if it helps your placement prep!
