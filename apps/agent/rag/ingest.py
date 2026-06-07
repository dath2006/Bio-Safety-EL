"""Document ingestion pipeline: chunk → embed → ChromaDB + pgvector."""

import uuid
from datetime import date
from pathlib import Path

import chromadb
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.models import RegulatoryChunk
from rag.chunker import DocumentChunk, parse_markdown_document
from rag.embeddings import embed_texts, has_openai_key

SOURCES_DIR = Path(__file__).parent / "sources"

# Registry of seed documents with metadata
DOCUMENT_REGISTRY: list[dict] = [
    {
        "file": "fssai_schedule4_part1_manufacturers.md",
        "source_body": "FSSAI",
        "document_title": "FSSAI Schedule 4 Part I — Food Manufacturers",
        "amendment_date": "2024-01-01",
        "product_categories": ["dairy", "dairy_pasteurized", "rte", "general"],
    },
    {
        "file": "fssai_schedule4_part4_food_service.md",
        "source_body": "FSSAI",
        "document_title": "FSSAI Schedule 4 Part IV — Food Service",
        "amendment_date": "2024-01-01",
        "product_categories": ["food_service", "catering", "street_food"],
    },
    {
        "file": "codex_cxc1_2020_food_hygiene.md",
        "source_body": "Codex",
        "document_title": "Codex CXC 1-1969 Rev. 2020 — General Principles of Food Hygiene",
        "amendment_date": "2020-06-01",
        "product_categories": ["general", "dairy", "dairy_pasteurized", "rte", "meat"],
    },
    {
        "file": "GENERAL PRINCIPLES.md",
        "source_body": "Codex",
        "document_title": "General Principles of Food Hygiene (CXC 1-1969)",
        "amendment_date": "2023-01-01",
        "product_categories": ["general", "dairy", "dairy_pasteurized", "rte", "meat", "seafood", "food_service", "packaged_food"],
    },
    {
        "file": "fssai_inspection_checklist_2022.md",
        "source_body": "FSSAI",
        "document_title": "FSSAI Inspection Checklist (Revised November 2022)",
        "amendment_date": "2022-11-01",
        "product_categories": ["general", "dairy", "dairy_pasteurized", "rte"],
    },
    {
        "file": "icmr_dairy_microbiological_standards.md",
        "source_body": "ICMR",
        "document_title": "ICMR Microbiological Standards for Dairy Products",
        "amendment_date": "2023-06-01",
        "product_categories": ["dairy", "dairy_pasteurized"],
    },
    # ── New documents (Fix 10) ─────────────────────────────────────────
    {
        "file": "fssai_schedule4_part2_transporters.md",
        "source_body": "FSSAI",
        "document_title": "FSSAI Schedule 4 Part II — Transporters and Cold Chain",
        "amendment_date": "2024-01-01",
        "product_categories": ["cold_chain", "dairy_pasteurized", "meat", "seafood", "rte"],
    },
    {
        "file": "fssai_microbiological_standards_2024.md",
        "source_body": "FSSAI",
        "document_title": "FSSAI Microbiological Standards for Food Products 2024",
        "amendment_date": "2024-03-01",
        "product_categories": [
            "dairy", "dairy_pasteurized", "meat", "seafood",
            "rte", "beverages", "packaged_food", "spices", "general",
        ],
    },
    {
        "file": "codex_cxc13_1969_meat_hygiene.md",
        "source_body": "Codex",
        "document_title": "Codex CXC 13-1969 — Code of Hygienic Practice for Meat",
        "amendment_date": "2020-01-01",
        "product_categories": ["meat", "rte", "general"],
    },
    {
        "file": "codex_cxc52_2003_seafood.md",
        "source_body": "Codex",
        "document_title": "Codex CXC 52-2003 — Code of Practice for Fish and Fishery Products",
        "amendment_date": "2013-01-01",
        "product_categories": ["seafood", "rte", "cold_chain", "general"],
    },
    {
        "file": "fssai_packaging_labelling_regulations.md",
        "source_body": "FSSAI",
        "document_title": "FSSAI Packaging and Labelling Regulations 2023",
        "amendment_date": "2023-08-01",
        "product_categories": [
            "packaged_food", "beverages", "dairy", "dairy_pasteurized",
            "meat", "seafood", "rte", "spices",
        ],
    },
    {
        "file": "codex_haccp_guidelines_2020.md",
        "source_body": "Codex",
        "document_title": "Codex HACCP System and Guidelines for Application (CXC 1-1969 Annex) 2020",
        "amendment_date": "2020-06-01",
        "product_categories": [
            "general", "dairy", "dairy_pasteurized", "meat", "seafood",
            "rte", "food_service", "catering", "packaged_food", "beverages",
            "spices", "street_food", "cold_chain",
        ],
    },
]



def load_static_document_chunks() -> list[DocumentChunk]:
    """Load and chunk all static registered seed documents (no DB required)."""
    settings = get_settings()
    all_chunks: list[DocumentChunk] = []
    for doc in DOCUMENT_REGISTRY:
        file_path = SOURCES_DIR / doc["file"]
        if not file_path.exists():
            continue
        chunks = parse_markdown_document(
            file_path=file_path,
            source_body=doc["source_body"],
            document_title=doc["document_title"],
            amendment_date=doc.get("amendment_date"),
            product_categories=doc.get("product_categories") or ["general"],
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        all_chunks.extend(chunks)
    return all_chunks


async def load_all_document_chunks(session: AsyncSession) -> list[DocumentChunk]:
    """Load and chunk all registered source documents, including dynamically uploaded ones."""
    settings = get_settings()
    all_chunks = load_static_document_chunks()

    # Fetch dynamic uploads from database
    from db.models import UploadedDocument
    from sqlalchemy import select
    
    query = select(UploadedDocument)
    res = await session.execute(query)
    dynamic_docs = res.scalars().all()
    
    for dd in dynamic_docs:
        amend_date = dd.amendment_date.isoformat() if dd.amendment_date else None
        file_path = SOURCES_DIR / dd.filename
        if not file_path.exists():
            continue
        chunks = parse_markdown_document(
            file_path=file_path,
            source_body=dd.source_body,
            document_title=dd.document_title,
            amendment_date=amend_date,
            # Ensure product_categories is never an empty list — default to 'general'
            product_categories=dd.product_categories or ["general"],
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        all_chunks.extend(chunks)

    return all_chunks


async def ingest_to_pgvector(
    session: AsyncSession,
    chunks: list[DocumentChunk],
    clear_existing: bool = True,
) -> int:
    """Embed chunks and store in PostgreSQL pgvector."""
    if clear_existing:
        await session.execute(delete(RegulatoryChunk))
        await session.flush()

    if not chunks:
        await session.commit()
        return 0

    texts = [c.text for c in chunks]
    embeddings: list[list[float] | None] = []
    if has_openai_key():
        embeddings = embed_texts(texts)
    else:
        embeddings = [None] * len(texts)

    for chunk, embedding in zip(chunks, embeddings):
        amendment = None
        if chunk.amendment_date:
            amendment = date.fromisoformat(chunk.amendment_date)

        record = RegulatoryChunk(
            id=uuid.uuid4(),
            source_body=chunk.source_body,
            document_title=chunk.document_title,
            section=chunk.section,
            text=chunk.text,
            embedding=embedding,
            amendment_date=amendment,
            product_categories=chunk.product_categories,
            hazard_types=chunk.hazard_types,
            chunk_metadata=chunk.metadata,
        )
        session.add(record)

    await session.commit()
    return len(chunks)


def ingest_to_chroma(
    chunks: list[DocumentChunk],
    clear_existing: bool = True,
) -> int:
    """Embed chunks and store in ChromaDB."""
    settings = get_settings()
    client = chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )

    if clear_existing:
        try:
            client.delete_collection(settings.chroma_collection)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )

    if not chunks:
        return 0

    texts = [c.text for c in chunks]
    if not has_openai_key():
        # ChromaDB semantic search needs embeddings; skip without OpenAI key.
        # Keyword fallback in retriever handles queries in dev mode.
        return 0

    embeddings = embed_texts(texts)
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "source_body": c.source_body,
            "document_title": c.document_title,
            "section": c.section,
            "amendment_date": c.amendment_date or "",
            # ChromaDB metadata cannot store Python lists — serialize to CSV strings.
            # Also guard against empty lists (ChromaDB rejects empty list values).
            "product_categories": ",".join(c.product_categories) if c.product_categories else "general",
            "hazard_types": ",".join(c.hazard_types) if c.hazard_types else "none",
        }
        for c in chunks
    ]

    # ChromaDB has batch limits; ingest in batches of 100
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            documents=texts[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    return len(chunks)


async def run_full_ingestion(
    session: AsyncSession,
    clear_existing: bool = True,
) -> dict[str, int]:
    """Run complete ingestion pipeline."""
    chunks = await load_all_document_chunks(session)
    pg_count = await ingest_to_pgvector(session, chunks, clear_existing)
    chroma_count = ingest_to_chroma(chunks, clear_existing)

    from db.models import UploadedDocument
    from sqlalchemy import func, select
    dynamic_count_query = select(func.count(UploadedDocument.id))
    dynamic_count_res = await session.execute(dynamic_count_query)
    dynamic_count = dynamic_count_res.scalar_one() or 0
    total_docs = len(DOCUMENT_REGISTRY) + dynamic_count

    return {
        "documents_processed": total_docs,
        "chunks_created": len(chunks),
        "pgvector_stored": pg_count,
        "chromadb_stored": chroma_count,
    }
