"""Tests for document chunking pipeline."""

from pathlib import Path

from rag.chunker import chunk_text, parse_markdown_document

SOURCES_DIR = Path(__file__).parent.parent / "rag" / "sources"


def test_chunk_text_overlap():
    text = "A" * 2000
    chunks = chunk_text(text, chunk_size=1500, chunk_overlap=300)
    assert len(chunks) >= 2
    assert all(len(c) <= 1500 for c in chunks)


def test_chunk_text_short():
    text = "Short regulatory text."
    chunks = chunk_text(text, chunk_size=1500, chunk_overlap=300)
    assert chunks == [text]


def test_parse_markdown_document():
    file_path = SOURCES_DIR / "fssai_schedule4_part1_manufacturers.md"
    chunks = parse_markdown_document(
        file_path=file_path,
        source_body="FSSAI",
        document_title="FSSAI Schedule 4 Part I",
        product_categories=["dairy_pasteurized"],
    )
    assert len(chunks) > 0
    assert all(c.source_body == "FSSAI" for c in chunks)
    assert any("pasteur" in c.text.lower() for c in chunks)


def test_hazard_type_inference():
    file_path = SOURCES_DIR / "icmr_dairy_microbiological_standards.md"
    chunks = parse_markdown_document(
        file_path=file_path,
        source_body="ICMR",
        document_title="ICMR Dairy Standards",
    )
    bio_chunks = [c for c in chunks if "biological" in c.hazard_types]
    assert len(bio_chunks) > 0
