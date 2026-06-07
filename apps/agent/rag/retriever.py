"""Hybrid retrieval: ChromaDB (fast) + pgvector (persistent, filterable)."""

from typing import Any

import chromadb
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.models import RegulatoryChunk
from rag.embeddings import embed_query, has_openai_key
from rag.keyword_search import keyword_retrieve
from rag.types import RetrievedChunk, format_citation


class RegulatoryRetriever:
    """Retrieve regulatory chunks from ChromaDB and pgvector."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._chroma_client: chromadb.HttpClient | None = None

    @property
    def chroma_client(self) -> chromadb.HttpClient:
        if self._chroma_client is None:
            self._chroma_client = chromadb.HttpClient(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
            )
        return self._chroma_client

    def get_chroma_collection(self):
        return self.chroma_client.get_or_create_collection(
            name=self.settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    async def retrieve_from_pgvector(
        self,
        session: AsyncSession,
        query: str,
        top_k: int | None = None,
        source_body: str | None = None,
        product_category: str | None = None,
        hazard_type: str | None = None,
    ) -> list[RetrievedChunk]:
        """Hybrid similarity + metadata filter search on pgvector."""
        top_k = top_k or self.settings.retrieval_top_k
        query_embedding = embed_query(query)

        filters = ["embedding IS NOT NULL"]
        params: dict[str, Any] = {
            "embedding": str(query_embedding),
            "top_k": top_k,
        }

        if source_body:
            filters.append("source_body = :source_body")
            params["source_body"] = source_body
        if product_category:
            filters.append("(:product_category = ANY(product_categories) OR 'general' = ANY(product_categories))")
            params["product_category"] = product_category
        if hazard_type:
            filters.append(":hazard_type = ANY(hazard_types)")
            params["hazard_type"] = hazard_type

        where_clause = " AND ".join(filters)
        sql = text(f"""
            SELECT id, source_body, document_title, section, text,
                   amendment_date, product_categories, hazard_types,
                   1 - (embedding <=> :embedding::vector) AS score
            FROM regulatory_chunks
            WHERE {where_clause}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        result = await session.execute(sql, params)
        rows = result.fetchall()

        return [
            RetrievedChunk(
                text=row.text,
                source_body=row.source_body,
                document_title=row.document_title,
                section=row.section,
                amendment_date=str(row.amendment_date) if row.amendment_date else None,
                product_categories=list(row.product_categories or []),
                hazard_types=list(row.hazard_types or []),
                score=float(row.score),
                citation=format_citation(row.source_body, row.document_title, row.section),
            )
            for row in rows
        ]

    def retrieve_from_chroma(
        self,
        query: str,
        top_k: int | None = None,
        source_body: str | None = None,
        product_category: str | None = None,
        hazard_type: str | None = None,
    ) -> list[RetrievedChunk]:
        """Fast in-session retrieval from ChromaDB."""
        top_k = top_k or self.settings.retrieval_top_k
        collection = self.get_chroma_collection()

        where_filter: dict[str, Any] | None = None
        conditions: list[dict[str, Any]] = []
        if source_body:
            conditions.append({"source_body": {"$eq": source_body}})
        if product_category:
            conditions.append({
                "$or": [
                    {"product_categories": {"$contains": product_category}},
                    {"product_categories": {"$contains": "general"}}
                ]
            })
        if hazard_type:
            conditions.append({"hazard_types": {"$contains": hazard_type}})
        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        query_embedding = embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[RetrievedChunk] = []
        if not results["documents"] or not results["documents"][0]:
            return chunks

        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = 1.0 - float(distance)
            chunks.append(
                RetrievedChunk(
                    text=doc,
                    source_body=meta.get("source_body", "FSSAI"),
                    document_title=meta.get("document_title", ""),
                    section=meta.get("section", ""),
                    amendment_date=meta.get("amendment_date"),
                    product_categories=meta.get("product_categories", []),
                    hazard_types=meta.get("hazard_types", []),
                    score=score,
                    citation=format_citation(
                        meta.get("source_body", ""),
                        meta.get("document_title", ""),
                        meta.get("section", ""),
                    ),
                )
            )

        return chunks

    async def retrieve(
        self,
        session: AsyncSession | None,
        query: str,
        top_k: int | None = None,
        source_body: str | None = None,
        product_category: str | None = None,
        hazard_type: str | None = None,
        prefer_pgvector: bool = False,
    ) -> list[RetrievedChunk]:
        """Retrieve from pgvector when session available, else ChromaDB."""
        if prefer_pgvector and session is not None:
            try:
                return await self.retrieve_from_pgvector(
                    session, query, top_k, source_body, product_category, hazard_type
                )
            except Exception:
                await session.rollback()

        try:
            results = self.retrieve_from_chroma(
                query, top_k, source_body, product_category, hazard_type
            )
            if results:
                return results
        except Exception:
            pass

        if session is not None:
            try:
                results = await self.retrieve_from_pgvector(
                    session, query, top_k, source_body, product_category, hazard_type
                )
                if results:
                    return results
            except Exception:
                await session.rollback()

        # Keyword fallback when vector stores are empty or unavailable
        return await keyword_retrieve(
            session,
            query,
            top_k or self.settings.retrieval_top_k,
            source_body,
            product_category,
            hazard_type,
        )

    async def count_chunks(self, session: AsyncSession) -> int:
        result = await session.execute(select(RegulatoryChunk.id))
        return len(result.scalars().all())


def chunks_to_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks as LLM context with citations."""
    if not chunks:
        return "No relevant regulatory documents found."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[Source {i}] {chunk.citation}\n"
            f"Relevance: {chunk.score:.2f}\n"
            f"{chunk.text}\n"
        )
    return "\n---\n".join(parts)
