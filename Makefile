.PHONY: dev-backend dev-frontend pair help

help:
	@echo "Watify dev targets:"
	@echo "  make dev-backend   start FastAPI on :8000 (uv + uvicorn)"
	@echo "  make dev-frontend  start Next.js on :3000 (npm)"
	@echo "  make pair          headless WhatsApp pairing (ASCII QR in terminal)"

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && \
	  if [ ! -d node_modules ]; then npm install --no-audit --no-fund; fi && \
	  npm run dev

pair:
	cd backend && uv run python scripts/pair.py
