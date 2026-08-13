import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.benchmark import evaluate_rag_mode
from app.rag.corpus.architecture import ARCHITECTURE_DOCS
from app.rag.corpus.postmortems import POSTMORTEMS
from app.rag.corpus.runbooks import RUNBOOKS
from app.rag.store import RAGStore


@pytest.mark.asyncio
async def test_rag_retrieval_benchmark_performance(db_session: AsyncSession) -> None:
    """IG-514 through IG-518: Evaluates recall, precision, MRR, NDCG, and latency."""
    store = RAGStore()

    # seed database
    for rb in RUNBOOKS:
        await store.add_document(
            db_session, rb["id"], rb["title"], rb["content"], category="runbook"
        )
    for pm in POSTMORTEMS:
        await store.add_document(
            db_session, pm["id"], pm["title"], pm["content"], category="postmortem"
        )
    for arch in ARCHITECTURE_DOCS:
        await store.add_document(
            db_session, arch["id"], arch["title"], arch["content"], category="architecture"
        )

    import json
    import os

    v_res = await evaluate_rag_mode(db_session, mode="vector", store=store)
    l_res = await evaluate_rag_mode(db_session, mode="lexical", store=store)
    h_res = await evaluate_rag_mode(db_session, mode="hybrid", store=store)

    assert h_res.query_count == 5
    assert h_res.recall_at_5 >= 0.8
    assert 0.0 <= h_res.precision_at_5 <= 1.0
    assert h_res.mrr >= 0.6

    os.makedirs("eval-results", exist_ok=True)
    report = {
        "vector_only": v_res.model_dump(),
        "lexical_only": l_res.model_dump(),
        "hybrid_rrf": h_res.model_dump(),
    }
    with open("eval-results/rag_benchmark.json", "w") as f:
        json.dump(report, f, indent=2)
