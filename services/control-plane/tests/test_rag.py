import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.chunker import chunk_text
from app.rag.embedder import cosine_similarity, generate_embedding
from app.rag.isolation import contains_ground_truth, sanitize_rag_chunk_metadata
from app.rag.store import RAGStore


def test_document_chunker_overlap() -> None:
    text = " ".join([f"word_{i}" for i in range(1000)])
    chunks = chunk_text(text, document_id="doc_1", chunk_size=500, overlap=50)
    assert len(chunks) >= 2
    assert chunks[0].token_count > 0
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_vector_embedding_similarity() -> None:
    v1 = generate_embedding("PostgreSQL database connection pool failure")
    v2 = generate_embedding("PostgreSQL DB connection pool timeout error")
    v3 = generate_embedding("Frontend React button hover state styling")

    sim_1_2 = cosine_similarity(v1, v2)
    sim_1_3 = cosine_similarity(v1, v3)

    assert sim_1_2 > sim_1_3
    assert len(v1) == 384


def test_ground_truth_isolation_guardrail() -> None:
    dirty_metadata = {
        "title": "Scenario 1 Metadata",
        "ground_truth": {"root_cause": "pool_exhaustion"},
        "primary_service": "inventory",
        "causal_chain": ["a", "b"],
    }
    assert contains_ground_truth(dirty_metadata) is True

    clean_metadata = sanitize_rag_chunk_metadata(dirty_metadata)
    assert contains_ground_truth(clean_metadata) is False
    assert "ground_truth" not in clean_metadata
    assert "primary_service" not in clean_metadata
    assert clean_metadata["title"] == "Scenario 1 Metadata"


@pytest.mark.asyncio
async def test_rag_hybrid_search(db_session: AsyncSession) -> None:
    store = RAGStore()

    # We must seed it first because previously RAGStore seeded on init
    from app.rag.corpus.runbooks import RUNBOOKS

    await store.add_document(
        db_session,
        RUNBOOKS[0]["id"],
        RUNBOOKS[0]["title"],
        RUNBOOKS[0]["content"],
        category="runbook",
    )

    results = await store.search_hybrid(db_session, "connection pool starvation", top_k=5)
    assert len(results) >= 1
    top_chunk, score = results[0]
    assert "pool" in top_chunk.content.lower()
    assert score > 0.0


@pytest.mark.asyncio
async def test_rag_metadata_filter(db_session: AsyncSession) -> None:
    store = RAGStore()
    await store.add_document(
        db_session,
        "filter-runbook",
        "Database recovery",
        "PostgreSQL database recovery connection pool saturation remediation",
        category="runbook",
    )
    await store.add_document(
        db_session,
        "filter-postmortem",
        "Database incident",
        "PostgreSQL database incident connection pool saturation analysis",
        category="postmortem",
    )

    results = await store.search_hybrid(
        db_session,
        "PostgreSQL connection pool saturation",
        metadata_filters={"category": "runbook"},
    )

    assert results
    assert {chunk.metadata["category"] for chunk, _score in results} == {"runbook"}
