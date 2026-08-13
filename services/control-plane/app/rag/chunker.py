import uuid
from typing import Any

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:10]}")
    document_id: str
    content: str
    chunk_index: int
    token_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


def count_tokens(text: str) -> int:
    # Approximate token count (approx 4 chars per token or space-separated words * 1.3)
    words = text.split()
    return max(1, int(len(words) * 1.2))


def chunk_text(
    text: str,
    document_id: str,
    chunk_size: int = 500,
    overlap: int = 50,
    metadata: dict[str, Any] | None = None,
) -> list[DocumentChunk]:
    words = text.split()
    if not words:
        return []

    meta = metadata or {}
    chunks: list[DocumentChunk] = []
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size

    chunk_idx = 0
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        chunk_str = " ".join(chunk_words)
        if not chunk_str.strip():
            continue

        chunks.append(
            DocumentChunk(
                document_id=document_id,
                content=chunk_str,
                chunk_index=chunk_idx,
                token_count=count_tokens(chunk_str),
                metadata=meta,
            )
        )
        chunk_idx += 1
        if i + chunk_size >= len(words):
            break

    return chunks
