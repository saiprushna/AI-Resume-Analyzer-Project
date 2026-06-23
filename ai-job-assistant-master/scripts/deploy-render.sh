#!/usr/bin/env bash
# Deploy AI Job Assistant to Render (or any Docker host).
#
# Render setup (manual):
#   1. New Web Service → connect GitHub repo
#   2. Environment: Docker
#   3. Add env var: GEMINI_API_KEY
#   4. Deploy
#
# Local Docker test:
#   docker build -t ai-job-assistant .
#   docker run -p 8000:8000 -e GEMINI_API_KEY=your-key ai-job-assistant

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Building Docker image..."
docker build -t ai-job-assistant .

echo ""
echo "==> Run locally:"
echo "docker run -p 8000:8000 -e GEMINI_API_KEY=\$GEMINI_API_KEY ai-job-assistant"
echo ""
echo "Open http://localhost:8000"
