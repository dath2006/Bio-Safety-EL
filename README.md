# AI-Powered HACCP Documentation & Regulatory Compliance System

Bio Safety Engineering — Major Academic Project

## Phase 1 Status

Phase 1 (Foundation & Intelligence Core) backend is implemented:

- FastAPI agent API with LangGraph orchestrator
- RAG pipeline (ChromaDB + pgvector)
- Seed regulatory knowledge base (FSSAI, Codex, ICMR)
- Hazard analysis agent with citations

See [PROGRESS.md](./PROGRESS.md) for detailed implementation tracking.
Frontend tasks are documented in [FRONTEND.md](./FRONTEND.md).

## Detailed Setup Guide

For an in-depth, step-by-step setup covering the Frontend (Vite/Bun), Backend (FastAPI), Docker Services (ChromaDB, Postgres, Redis), and knowledge ingestion instruction (including `GENERAL PRINCIPLES.md`), please refer to [**SETUP.md**](./SETUP.md).

## Quick Start

### Prerequisites

- Docker Desktop
- Python 3.12+
- OpenRouter API key (for LLM — model `z-ai/glm-5`)
- OpenAI API key (for embeddings)

### 1. Start infrastructure

```bash
docker compose up -d
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Install agent dependencies

```bash
cd apps/agent
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 4. Ingest knowledge base

```bash
python scripts/ingest.py
```

### 5. Start agent API

```bash
python main.py
```

API docs: http://localhost:8000/docs

### 6. Demo milestone query

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What are the biological hazards in pasteurization of milk per FSSAI?\", \"product_category\": \"dairy_pasteurized\"}"
```

## Project Structure

```
haccp-system/
├── apps/
│   ├── agent/          # FastAPI + LangGraph backend (Phase 1 ✅)
│   └── web/            # Next.js frontend (Phase 1 — see FRONTEND.md)
├── packages/
│   └── shared-types/   # Shared TypeScript types
├── docker-compose.yml
└── docs/
```

## Run Tests

```bash
cd apps/agent
pytest -v
```
