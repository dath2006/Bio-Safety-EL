"""Document chunking with metadata tagging per blueprint spec."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DocumentChunk:
    text: str
    source_body: str
    document_title: str
    section: str
    amendment_date: str | None = None
    product_categories: list[str] = field(default_factory=list)
    hazard_types: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_text(
    text: str,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
) -> list[str]:
    """Split text into overlapping character windows."""
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - chunk_overlap

    return chunks


def parse_markdown_document(
    file_path: Path,
    source_body: str,
    document_title: str,
    amendment_date: str | None = None,
    product_categories: list[str] | None = None,
    hazard_types: list[str] | None = None,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
) -> list[DocumentChunk]:
    """Parse a markdown file into section-aware chunks with metadata."""
    content = file_path.read_text(encoding="utf-8")
    sections = _split_markdown_sections(content)
    all_chunks: list[DocumentChunk] = []

    for section_heading, section_text in sections:
        for chunk_text_value in chunk_text(section_text, chunk_size, chunk_overlap):
            all_chunks.append(
                DocumentChunk(
                    text=chunk_text_value,
                    source_body=source_body,
                    document_title=document_title,
                    section=section_heading,
                    amendment_date=amendment_date,
                    product_categories=product_categories or [],
                    hazard_types=hazard_types or _infer_hazard_types(chunk_text_value),
                    metadata={"file": file_path.name},
                )
            )

    return all_chunks


def _split_markdown_sections(content: str) -> list[tuple[str, str]]:
    """Split markdown by ## headings; preamble becomes 'Introduction'."""
    lines = content.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    return [(h, "\n".join(body).strip()) for h, body in sections if "\n".join(body).strip()]


def _infer_hazard_types(text: str) -> list[str]:
    """Infer hazard type tags from chunk content."""
    text_lower = text.lower()
    types: list[str] = []
    if any(
        kw in text_lower
        for kw in ("pathogen", "bacteria", "microbial", "biological", "allergen", "virus")
    ):
        types.append("biological")
    if any(
        kw in text_lower
        for kw in ("chemical", "pesticide", "heavy metal", "aflatoxin", "contaminant")
    ):
        types.append("chemical")
    if any(
        kw in text_lower
        for kw in ("physical", "metal fragment", "glass", "foreign object", "bone")
    ):
        types.append("physical")
    if not types:
        types.append("general")
    return types
