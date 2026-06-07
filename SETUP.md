# HACCP AI System - Detailed Setup Guide

This guide provides step-by-step instructions to set up the complete environment for the Bio Safety Engineering HACCP AI system, including the Docker infrastructure, the FastAPI AI agent backend, the TanStack Start frontend, and how to ingest regulatory documents like `GENERAL PRINCIPLES.md`.

## 1. Infrastructure Setup (Docker)

The application requires PostgreSQL (with `pgvector`), Redis, and ChromaDB. These are all orchestrated via Docker Compose.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine + Docker Compose

### Starting the Infrastructure

From the root of the project, run:

```bash
docker compose up -d
```

**Services Started:**

- **Postgres (`haccp-postgres`)**: Runs on port `5432`. Used for application data and vector embeddings via `pgvector`. (Configured with `POSTGRES_DB: haccp_db`).
- **Redis (`haccp-redis`)**: Runs on port `6379`. Used for task queues and caching.
- **ChromaDB (`haccp-chromadb`)**: Runs on port `8001`. The main vector database used by LangChain/RAG.

_Note: Data volumes (`postgres_data`, `redis_data`, `chroma_data`) will persist across container restarts._

---

## 2. Backend Setup (FastAPI + LangGraph)

The backend agent is a Python 3.12+ application that provides a FastAPI and integrates LangGraph and RAG workflows.

### Prerequisites

- Python 3.12+

### Installation Steps

1. **Navigate to the agent directory**:

   ```bash
   cd apps/agent
   ```

2. **Create and activate a virtual environment**:
   - **Windows**:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **Mac/Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` (or create a `.env` in the `apps/agent` folder) and fill in your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   DATABASE_URL=postgresql+asyncpg://haccp:haccp_dev_password@localhost:5432/haccp_db
   REDIS_URL=redis://localhost:6379/0
   CHROMA_URL=http://localhost:8001
   ```

### Running the API

Once configured, you can start the backend service:

```bash
python main.py
```

The API is available at `http://localhost:8000`. You can view the Auto-Generated Swagger documentation at `http://localhost:8000/docs`.

---

## 3. Knowledge Base & Document Ingestion (e.g., `GENERAL PRINCIPLES.md`)

The system uses a Retrieval-Augmented Generation (RAG) architecture. Source documents are stored as `.md` files in `apps/agent/rag/sources/`.

### How Ingestion Works

The `scripts/ingest.py` script reads from the `DOCUMENT_REGISTRY` defined in `apps/agent/rag/ingest.py`, chunks the Markdown text, embeds it using OpenAI, and stores the vectors in ChromaDB and Postgres.

### Ingesting `GENERAL PRINCIPLES.md`

The `GENERAL PRINCIPLES.md` (Codex CXC 1-1969) document has already been placed in `apps/agent/rag/sources/GENERAL PRINCIPLES.md`.

To ingest it:

1. Ensure the backend infrastructure (Docker) is up and running.
2. In `apps/agent/rag/ingest.py`, verify the file is added to the `DOCUMENT_REGISTRY`. (We have just added it!)
3. From the `apps/agent/` directory, run the script:
   ```bash
   python scripts/ingest.py
   ```
   _This will parse, chunk, embed, and store the contents of all documents in the registry into your local databases. Wait for it to report `Ingestion complete`._

---

## 4. Frontend Setup

The frontend is a modern web application built using TanStack Start, React, Vite, and Tailwind CSS. It uses `bun` as the package manager.

### Prerequisites

- Node.js (v20+)

### Installation Steps

1. **Navigate to the frontend directory**:

   ```bash
   cd apps/client
   ```

2. **Install dependencies**:

   ```bash
   npm install --force --legacy-peer-deps
   ```

3. **Configure environment**:
   Copy `.env.example` to `.env` and fill in any necessary variables (if applicable).

4. **Start the development server**:
   ```bash
   npm run dev
   ```

The frontend will start in development mode, typically accessible on `http://localhost:5173` or `http://localhost:3000` (check your console output).

### Frontend Workflow Tips

As per standard preferences, try to run targeted tooling (like eslint, type checking) on exactly what's changed, rather than a full `npm run build` after every single modification.

To run checks without building:

```bash
npm run lint
```
