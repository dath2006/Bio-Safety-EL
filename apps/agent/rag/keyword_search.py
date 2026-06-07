"""Keyword-based retrieval fallback when embeddings/API keys are unavailable."""

import re

from sqlalchemy.ext.asyncio import AsyncSession

from rag.chunker import DocumentChunk
from rag.ingest import load_all_document_chunks, load_static_document_chunks
from rag.types import RetrievedChunk, format_citation

_cached_chunks: list[DocumentChunk] | None = None


async def _get_chunks(session: AsyncSession | None = None) -> list[DocumentChunk]:
    global _cached_chunks
    if _cached_chunks is None:
        if session is not None:
            _cached_chunks = await load_all_document_chunks(session)
        else:
            _cached_chunks = load_static_document_chunks()
    return _cached_chunks


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _score_chunk(query: str, chunk: DocumentChunk) -> float:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    text_tokens = _tokenize(chunk.text + " " + chunk.section + " " + chunk.document_title)
    overlap = len(query_tokens & text_tokens)
    base = overlap / len(query_tokens)

    # Boost exact phrase fragments
    query_lower = query.lower()
    text_lower = chunk.text.lower()
    for phrase in re.findall(r"\w+(?:\s+\w+){1,3}", query_lower):
        if phrase in text_lower:
            base += 0.15

    return min(base, 1.0)


async def keyword_retrieve(
    session: AsyncSession | None,
    query: str,
    top_k: int = 5,
    source_body: str | None = None,
    product_category: str | None = None,
    hazard_type: str | None = None,
) -> list[RetrievedChunk]:
    """Score in-memory document chunks by keyword overlap."""
    scored: list[tuple[float, DocumentChunk]] = []

    chunks = await _get_chunks(session)
    for chunk in chunks:
        if source_body and chunk.source_body != source_body:
            continue
        if (
            product_category
            and chunk.product_categories
            and product_category not in chunk.product_categories
            and "general" not in chunk.product_categories
        ):
            continue
        if (
            hazard_type
            and chunk.hazard_types
            and hazard_type not in chunk.hazard_types
        ):
            continue

        score = _score_chunk(query, chunk)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        RetrievedChunk(
            text=chunk.text,
            source_body=chunk.source_body,
            document_title=chunk.document_title,
            section=chunk.section,
            amendment_date=chunk.amendment_date,
            product_categories=chunk.product_categories,
            hazard_types=chunk.hazard_types,
            score=score,
            citation=format_citation(chunk.source_body, chunk.document_title, chunk.section),
        )
        for score, chunk in scored[:top_k]
    ]
