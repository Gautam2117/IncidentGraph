#!/usr/bin/env python3
"""Run the production PostgreSQL/pgvector/FTS/RRF retrieval benchmark."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.rag.benchmark import EVAL_QUERIES, evaluate_rag_mode
from app.rag.corpus.architecture import ARCHITECTURE_DOCS
from app.rag.corpus.postmortems import POSTMORTEMS
from app.rag.corpus.runbooks import RUNBOOKS
from app.rag.store import RAGStore


async def run(output: Path) -> dict[str, object]:
    store = RAGStore()
    async with AsyncSessionLocal() as session:
        extension = await session.scalar(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
        if extension is None:
            raise RuntimeError("pgvector extension is not installed")

        for category, documents in (
            ("runbook", RUNBOOKS),
            ("postmortem", POSTMORTEMS),
            ("architecture", ARCHITECTURE_DOCS),
        ):
            for document in documents:
                await store.add_document(
                    session,
                    document["id"],
                    document["title"],
                    document["content"],
                    category=category,
                    metadata={"benchmark_corpus": True},
                )

        results = {
            mode: (await evaluate_rag_mode(session, mode=mode, store=store)).model_dump()
            for mode in ("vector", "lexical", "hybrid")
        }

    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "execution_mode": "production-path-local-embedding",
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "database_backend": "PostgreSQL pgvector + FTS",
        "pgvector_version": str(extension),
        "query_count": len(EVAL_QUERIES),
        "vector_only": results["vector"],
        "lexical_only": results["lexical"],
        "hybrid_rrf": results["hybrid"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("eval-results/rag_benchmark.json"))
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(args.output)), indent=2))


if __name__ == "__main__":
    main()
