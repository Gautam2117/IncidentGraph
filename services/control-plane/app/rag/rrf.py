from collections import defaultdict

from app.rag.chunker import DocumentChunk


def hybrid_rrf_search(
    vector_results: list[tuple[DocumentChunk, float]],
    lexical_results: list[tuple[DocumentChunk, float]],
    k: int = 60,
    top_n: int = 10,
) -> list[tuple[DocumentChunk, float]]:
    """Combines vector similarity ranks and lexical (BM25) ranks using Reciprocal Rank Fusion."""
    rrf_scores: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, DocumentChunk] = {}

    # Rank vector results (1-indexed)
    for rank, (chunk, _score) in enumerate(vector_results, start=1):
        chunk_map[chunk.chunk_id] = chunk
        rrf_scores[chunk.chunk_id] += 1.0 / (k + rank)

    # Rank lexical results (1-indexed)
    for rank, (chunk, _score) in enumerate(lexical_results, start=1):
        chunk_map[chunk.chunk_id] = chunk
        rrf_scores[chunk.chunk_id] += 1.0 / (k + rank)

    # Sort by combined RRF score descending
    sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [(chunk_map[chk_id], rrf_score) for chk_id, rrf_score in sorted_chunks[:top_n]]
