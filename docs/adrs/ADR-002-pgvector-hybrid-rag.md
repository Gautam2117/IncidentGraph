# ADR-002: PostgreSQL + pgvector Hybrid RAG for Operational Knowledge

## Context
Operational knowledge (runbooks, postmortems, ownership manifests, deployment histories) requires both exact keyword matching (e.g., error codes, service names, deployment IDs) and semantic query capabilities.

## Decision
We implement a **Hybrid RAG engine** combining PostgreSQL `pgvector` dense embeddings with Postgres Full-Text Search (FTS) lexical matching, fused using Reciprocal Rank Fusion (RRF).

## Status
Accepted

## Consequences
- Single unified storage layer in PostgreSQL avoiding specialized external vector DB overhead.
- Superior recall on technical terms (error strings, metrics names) via FTS combined with semantic understanding via vector similarity.
