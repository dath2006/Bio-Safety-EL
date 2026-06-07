# Architecture Decision Record: RAG Strategy (ChromaDB + pgvector)

## Status
Accepted

## Context
The HACCP AI System requires a robust Retrieval-Augmented Generation (RAG) pipeline to provide accurate, cited regulatory information to the LLM. The system must support:
1. Fast semantic search for chat and interactive queries
2. Persistent, transactional storage for document metadata, chunk text, and vector embeddings linked to the core PostgreSQL database
3. Graceful degradation when OpenAI API keys (for text embeddings) are unavailable (e.g., during local development or demo scenarios)

## Decision
We implemented a **dual-storage RAG architecture**:

### 1. ChromaDB (Primary Retrieval Engine)
- Serves as the primary semantic search engine for the LangGraph agent.
- Provides extremely fast `HNSW` (Hierarchical Navigable Small World) index-based similarity search.
- Used for the `/api/chat` and `/api/search` endpoints.
- Handled via the `langchain-chroma` integration.

### 2. PostgreSQL + pgvector (Source of Truth & Persistence)
- Serves as the durable system of record for all ingested regulatory chunks.
- The `RegulatoryChunk` table in PostgreSQL stores the raw text, section metadata, amendment dates, product categories, and the vector embedding (using the `pgvector` extension).
- Allows relational queries (e.g., "Find all chunks updated after 2023 for 'meat' category") combined with vector similarity.

### 3. Graceful Fallback (Keyword Search)
- If the `OPENAI_API_KEY` is not present, the ingestion pipeline skips vector generation but still stores the raw text and metadata in PostgreSQL and ChromaDB (without embeddings).
- The `rag/retriever.py` module detects the absence of embeddings and falls back to a PostgreSQL `ILIKE` keyword-matching search across the `text` and `document_title` columns.

## Consequences

**Positive:**
- **Reliability:** If ChromaDB goes down or its volume is lost, the entire index can be instantly rebuilt from the `pgvector` source of truth.
- **Flexibility:** Developers can run the system locally without an OpenAI key to test the graph logic using keyword retrieval.
- **Relational Integrity:** Uploaded custom documents (`UploadedDocument` table) are transactionally linked to their generated chunks. Deleting a document securely cascades to remove its chunks from pgvector, followed by a ChromaDB sync.

**Negative:**
- **Storage Duplication:** Vector embeddings and chunk text are stored twice (once in Postgres, once in ChromaDB), increasing disk usage. Given the domain (regulatory text is ~10s of MBs), this is negligible.
- **Ingestion Overhead:** Writing to two data stores takes slightly longer, though ingestion is an infrequent administrative task.

## Implementation Details
- Ingestion script: `apps/agent/rag/ingest.py`
- Database schema: `apps/agent/db/models.py` (`RegulatoryChunk` model)
- Search logic: `apps/agent/rag/retriever.py`
