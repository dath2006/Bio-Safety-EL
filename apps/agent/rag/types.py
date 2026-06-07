"""Shared RAG types."""

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    text: str
    source_body: str
    document_title: str
    section: str
    amendment_date: str | None
    product_categories: list[str]
    hazard_types: list[str]
    score: float
    citation: str


def format_citation(source_body: str, document_title: str, section: str) -> str:
    parts = [p for p in [source_body, document_title, section] if p]
    return " — ".join(parts)
