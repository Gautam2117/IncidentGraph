import hashlib
import re
from typing import Any

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.knowledge_models import KnowledgeChunk, KnowledgeDocument
from app.rag.chunker import DocumentChunk, chunk_text, count_tokens
from app.rag.provider import EmbeddingProvider, create_embedding_provider
from app.rag.rrf import hybrid_rrf_search


class RAGStore:
    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self.provider = provider or create_embedding_provider()

    async def add_document(
        self,
        session: AsyncSession,
        doc_id: str,
        title: str,
        content: str,
        category: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        meta = metadata or {}
        # Simple content hash for deduplication
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if already exists
        existing = await session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.content_hash == content_hash)
        )
        if existing.scalar_one_or_none():
            return 0  # Already indexed

        previous_version = await session.scalar(
            select(func.max(KnowledgeDocument.version)).where(
                KnowledgeDocument.source_uri == doc_id
            )
        )
        await session.execute(
            update(KnowledgeDocument)
            .where(
                KnowledgeDocument.source_uri == doc_id,
                KnowledgeDocument.status == "active",
            )
            .values(status="archived")
        )

        doc = KnowledgeDocument(
            title=title,
            source_uri=doc_id,
            content=content,
            content_hash=content_hash,
            status="active",
            version=(previous_version or 0) + 1,
            metadata_json={"category": category, **meta},
        )
        session.add(doc)
        await session.flush()  # get doc.id

        chunks = chunk_text(
            content,
            document_id=doc_id,
            chunk_size=500,
            overlap=50,
            metadata={"title": title, "category": category, **meta},
        )

        chunk_models = []
        for i, chunk in enumerate(chunks):
            embedding = await self.provider.embed_text(chunk.content)
            chunk_models.append(
                KnowledgeChunk(
                    document_id=doc.id, content=chunk.content, chunk_index=i, embedding=embedding
                )
            )

        session.add_all(chunk_models)
        await session.commit()
        return len(chunks)

    async def search_vector(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        query_vector = await self.provider.embed_text(query)
        # using pgvector `<=>` for cosine distance
        stmt = (
            select(
                KnowledgeChunk,
                KnowledgeChunk.embedding.cosine_distance(query_vector).label("distance"),
            )
            .join(KnowledgeDocument)
            .where(KnowledgeDocument.status == "active")
            .options(selectinload(KnowledgeChunk.document))
            .order_by(text("distance ASC"))
            .limit(top_k)
        )
        if metadata_filters:
            stmt = stmt.where(KnowledgeDocument.metadata_json.contains(metadata_filters))
        result = await session.execute(stmt)

        res: list[tuple[DocumentChunk, float]] = []
        for row in result:
            chunk: KnowledgeChunk = row[0]
            distance = row[1]
            similarity = 1.0 - float(distance)

            doc_chunk = DocumentChunk(
                chunk_id=str(chunk.id),
                document_id=chunk.document.source_uri or str(chunk.document_id),
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                token_count=count_tokens(chunk.content),
                metadata=chunk.document.metadata_json,
            )
            res.append((doc_chunk, similarity))

        return res

    async def search_lexical(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        # PostgreSQL web search joins plain tokens with AND. Diagnostic prompts
        # are long, so use OR candidates and let ts_rank order their relevance.
        terms = re.findall(r"[A-Za-z0-9_]+", query)
        lexical_query = " OR ".join(dict.fromkeys(terms)) or query
        stmt = (
            select(
                KnowledgeChunk,
                text("ts_rank(fts_vector, websearch_to_tsquery('english', :query)) AS rank"),
            )
            .join(KnowledgeDocument)
            .options(selectinload(KnowledgeChunk.document))
            .where(
                KnowledgeDocument.status == "active",
                text("fts_vector @@ websearch_to_tsquery('english', :query)"),
            )
            .params(query=lexical_query)
            .order_by(text("rank DESC"))
            .limit(top_k)
        )
        if metadata_filters:
            stmt = stmt.where(KnowledgeDocument.metadata_json.contains(metadata_filters))
        result = await session.execute(stmt)

        res: list[tuple[DocumentChunk, float]] = []
        for row in result:
            chunk: KnowledgeChunk = row[0]
            rank = row[1]

            doc_chunk = DocumentChunk(
                chunk_id=str(chunk.id),
                document_id=chunk.document.source_uri or str(chunk.document_id),
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                token_count=count_tokens(chunk.content),
                metadata=chunk.document.metadata_json,
            )
            res.append((doc_chunk, float(rank)))

        return res

    async def search_hybrid(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 10,
        metadata_filters: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        v_results = await self.search_vector(
            session, query, top_k=top_k * 2, metadata_filters=metadata_filters
        )
        l_results = await self.search_lexical(
            session, query, top_k=top_k * 2, metadata_filters=metadata_filters
        )
        res: list[tuple[DocumentChunk, float]] = hybrid_rrf_search(
            v_results, l_results, top_n=top_k
        )
        return res


_global_rag_store: RAGStore | None = None


def get_rag_store() -> RAGStore:
    global _global_rag_store
    if _global_rag_store is None:
        _global_rag_store = RAGStore()
    return _global_rag_store
