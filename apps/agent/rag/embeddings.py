"""Embedding provider abstraction."""

import hashlib

from langchain_openai import OpenAIEmbeddings

from config import get_settings


def has_openai_key() -> bool:
    return bool(get_settings().openai_api_key.strip())


def get_embedding_model() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        api_key=settings.openai_api_key or None,
    )


def _dev_hash_embed(text: str, dim: int = 1536) -> list[float]:
    """Deterministic local embedding for dev/demo without OpenAI API key."""
    vec: list[float] = []
    seed = text.encode("utf-8")
    idx = 0
    while len(vec) < dim:
        digest = hashlib.sha256(seed + idx.to_bytes(4, "little")).digest()
        idx += 1
        for byte_val in digest:
            if len(vec) >= dim:
                break
            # Map byte to [-1, 1] — always finite, never NaN
            vec.append((byte_val / 127.5) - 1.0)
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts."""
    if not texts:
        return []
    if has_openai_key():
        model = get_embedding_model()
        return model.embed_documents(texts)
    return [_dev_hash_embed(t, get_settings().embedding_dimensions) for t in texts]


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    if has_openai_key():
        model = get_embedding_model()
        return model.embed_query(query)
    return _dev_hash_embed(query, get_settings().embedding_dimensions)
