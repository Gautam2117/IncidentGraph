import math
import time
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.store import RAGStore, get_rag_store


class RAGEvalResult(BaseModel):
    query_count: int
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    precision_at_1: float
    precision_at_5: float
    precision_at_10: float
    mrr: float
    ndcg_at_10: float
    mean_latency_ms: float


EVAL_QUERIES: list[dict[str, Any]] = [
    {
        "query": "PostgreSQL connection pool exhausted active connections max pool size",
        "expected_doc_ids": ["rb_db_pool_exhaustion", "pm_001"],
    },
    {
        "query": "Payment gateway latency response 3000ms circuit breaker",
        "expected_doc_ids": ["rb_payment_gateway_latency", "pm_002"],
    },
    {
        "query": "JWT token secret mismatch auth invalid signature 401",
        "expected_doc_ids": ["rb_auth_errors", "pm_003"],
    },
    {
        "query": "N+1 query pattern selectinload eager loading orders",
        "expected_doc_ids": ["rb_n_plus_one_query", "pm_004"],
    },
    {
        "query": "Redis memory growth LRU key eviction TTL",
        "expected_doc_ids": ["rb_redis_latency", "pm_005"],
    },
]


def compute_dcg(retrieved_ids: list[str], expected_ids: set[str], k: int = 10) -> float:
    dcg = 0.0
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        rel = 1.0 if doc_id in expected_ids else 0.0
        dcg += rel / math.log2(rank + 1)
    return dcg


def compute_idcg(expected_count: int, k: int = 10) -> float:
    idcg = 0.0
    for rank in range(1, min(expected_count, k) + 1):
        idcg += 1.0 / math.log2(rank + 1)
    return idcg


async def evaluate_rag_mode(
    session: AsyncSession, mode: str = "hybrid", store: RAGStore | None = None
) -> RAGEvalResult:
    rag_store = store or get_rag_store()

    recall1_hits = 0
    recall5_hits = 0
    recall10_hits = 0
    precision1_sum = 0.0
    precision5_sum = 0.0
    precision10_sum = 0.0
    mrr_sum = 0.0
    ndcg_sum = 0.0
    latencies: list[float] = []

    for item in EVAL_QUERIES:
        query = item["query"]
        expected_set = set(item["expected_doc_ids"])

        t0 = time.perf_counter()
        if mode == "vector":
            results = await rag_store.search_vector(session, query, top_k=10)
        elif mode == "lexical":
            results = await rag_store.search_lexical(session, query, top_k=10)
        else:
            results = await rag_store.search_hybrid(session, query, top_k=10)
        latencies.append((time.perf_counter() - t0) * 1000.0)

        retrieved_doc_ids = [chunk.document_id for chunk, _score in results]

        # Recall@k
        if any(doc_id in expected_set for doc_id in retrieved_doc_ids[:1]):
            recall1_hits += 1
        if any(doc_id in expected_set for doc_id in retrieved_doc_ids[:5]):
            recall5_hits += 1
        if any(doc_id in expected_set for doc_id in retrieved_doc_ids[:10]):
            recall10_hits += 1

        # Precision@k. Retrieval is chunk-level, so repeated relevant chunks are
        # each counted as relevant results, which matches what enters context.
        precision1_sum += sum(doc_id in expected_set for doc_id in retrieved_doc_ids[:1]) / 1
        precision5_sum += sum(doc_id in expected_set for doc_id in retrieved_doc_ids[:5]) / 5
        precision10_sum += sum(doc_id in expected_set for doc_id in retrieved_doc_ids[:10]) / 10

        # MRR (Mean Reciprocal Rank)
        rr = 0.0
        for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
            if doc_id in expected_set:
                rr = 1.0 / rank
                break
        mrr_sum += rr

        # NDCG@10
        dcg = compute_dcg(retrieved_doc_ids, expected_set, k=10)
        idcg = compute_idcg(len(expected_set), k=10)
        ndcg_sum += (dcg / idcg) if idcg > 0 else 0.0

    n = len(EVAL_QUERIES)
    return RAGEvalResult(
        query_count=n,
        recall_at_1=round(recall1_hits / n, 4),
        recall_at_5=round(recall5_hits / n, 4),
        recall_at_10=round(recall10_hits / n, 4),
        precision_at_1=round(precision1_sum / n, 4),
        precision_at_5=round(precision5_sum / n, 4),
        precision_at_10=round(precision10_sum / n, 4),
        mrr=round(mrr_sum / n, 4),
        ndcg_at_10=round(ndcg_sum / n, 4),
        mean_latency_ms=round(sum(latencies) / n, 2),
    )


async def evaluate_rag_retrieval(
    session: AsyncSession, store: RAGStore | None = None
) -> RAGEvalResult:
    return await evaluate_rag_mode(session, mode="hybrid", store=store)
