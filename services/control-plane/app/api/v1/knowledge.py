import hashlib
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import UserProfile, UserRole, require_role
from app.db.models.audit_models import AuditEvent
from app.db.models.knowledge_models import KnowledgeDocument
from app.db.session import get_db
from app.rag.store import get_rag_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeDocumentRequest(BaseModel):
    source_uri: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=1_000_000)
    category: str = Field(default="general", min_length=1, max_length=100)
    metadata: dict[str, object] = Field(default_factory=dict)


class KnowledgeDocumentDTO(BaseModel):
    id: str
    source_uri: str | None
    title: str
    content: str
    category: str
    status: str
    version: int
    chunk_count: int
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    mode: str = Field(default="hybrid", pattern=r"^(vector|lexical|hybrid)$")
    top_k: int = Field(default=10, ge=1, le=50)


class KnowledgeSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, object]


def _to_dto(document: KnowledgeDocument) -> KnowledgeDocumentDTO:
    return KnowledgeDocumentDTO(
        id=str(document.id),
        source_uri=document.source_uri,
        title=document.title,
        content=document.content,
        category=str(document.metadata_json.get("category", "general")),
        status=document.status,
        version=document.version,
        chunk_count=len(document.chunks),
        metadata=document.metadata_json,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get("", response_model=list[KnowledgeDocumentDTO])
async def list_knowledge_documents(
    include_archived: bool = Query(default=False),
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> list[KnowledgeDocumentDTO]:
    statement = select(KnowledgeDocument).options(selectinload(KnowledgeDocument.chunks))
    if not include_archived:
        statement = statement.where(KnowledgeDocument.status == "active")
    statement = statement.order_by(KnowledgeDocument.updated_at.desc())
    documents = (await session.execute(statement)).scalars().all()
    return [_to_dto(document) for document in documents]


@router.post("", response_model=KnowledgeDocumentDTO, status_code=status.HTTP_201_CREATED)
async def ingest_knowledge_document(
    request: KnowledgeDocumentRequest,
    session: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> KnowledgeDocumentDTO:
    store = get_rag_store()
    await store.add_document(
        session,
        doc_id=request.source_uri,
        title=request.title,
        content=request.content,
        category=request.category,
        metadata=request.metadata,
    )
    content_hash = hashlib.sha256(request.content.encode()).hexdigest()
    document = await session.scalar(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.content_hash == content_hash)
        .options(selectinload(KnowledgeDocument.chunks))
    )
    if document is None:
        raise RuntimeError("Knowledge ingestion completed without a document record")
    session.add(
        AuditEvent(
            actor=user.email,
            action="knowledge.ingest",
            resource_type="knowledge_document",
            resource_id=str(document.id),
            details={"source_uri": request.source_uri, "version": document.version},
        )
    )
    response = _to_dto(document)
    await session.commit()
    return response


@router.post("/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> list[KnowledgeSearchResult]:
    store = get_rag_store()
    if request.mode == "vector":
        results = await store.search_vector(session, request.query, top_k=request.top_k)
    elif request.mode == "lexical":
        results = await store.search_lexical(session, request.query, top_k=request.top_k)
    else:
        results = await store.search_hybrid(session, request.query, top_k=request.top_k)
    return [
        KnowledgeSearchResult(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            content=chunk.content,
            score=round(score, 6),
            metadata=chunk.metadata,
        )
        for chunk, score in results
    ]


async def _get_document(session: AsyncSession, document_id: str) -> KnowledgeDocument:
    try:
        uid = uuid.UUID(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found") from exc
    document = await session.scalar(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.id == uid)
        .options(selectinload(KnowledgeDocument.chunks))
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return document


@router.get("/{document_id}", response_model=KnowledgeDocumentDTO)
async def get_knowledge_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> KnowledgeDocumentDTO:
    return _to_dto(await _get_document(session, document_id))


@router.post("/{document_id}/reindex", response_model=KnowledgeDocumentDTO)
async def reindex_knowledge_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> KnowledgeDocumentDTO:
    document = await _get_document(session, document_id)
    store = get_rag_store()
    for chunk in document.chunks:
        chunk.embedding = await store.provider.embed_text(chunk.content)
    session.add(
        AuditEvent(
            actor=user.email,
            action="knowledge.reindex",
            resource_type="knowledge_document",
            resource_id=document_id,
            details={"chunk_count": len(document.chunks)},
        )
    )
    response = _to_dto(document)
    await session.commit()
    return response


@router.delete("/{document_id}", response_model=KnowledgeDocumentDTO)
async def archive_knowledge_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> KnowledgeDocumentDTO:
    document = await _get_document(session, document_id)
    document.status = "archived"
    session.add(
        AuditEvent(
            actor=user.email,
            action="knowledge.archive",
            resource_type="knowledge_document",
            resource_id=document_id,
            details={},
        )
    )
    response = _to_dto(document)
    await session.commit()
    return response
