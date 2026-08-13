'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { archiveKnowledgeDocument, fetchKnowledge, KnowledgeDocument, reindexKnowledgeDocument } from '@/lib/api';

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [error, setError] = useState<string | null>(null);
  const load = () => fetchKnowledge(true).then(setDocuments).catch((e: Error) => setError(e.message));
  useEffect(() => { void load(); }, []);
  async function act(id: string, type: 'reindex' | 'archive') { try { type === 'reindex' ? await reindexKnowledgeDocument(id) : await archiveKnowledgeDocument(id); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Action failed'); } }
  return <div className="space-y-6">
    <header><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Retrieval corpus</p><h1 className="mt-2 text-3xl font-semibold text-white">Knowledge index</h1><p className="mt-2 text-sm text-slate-400">Versioned runbooks and postmortems indexed with PostgreSQL full-text search, pgvector HNSW, and reciprocal-rank fusion.</p></header>
    {error && <div className="rounded-lg border border-rose-900 bg-rose-950/30 p-3 text-sm text-rose-300">{error}</div>}
    <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-900/40"><table className="w-full text-left text-sm"><thead className="bg-white/[0.03] text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="p-4">Document</th><th className="p-4">Version</th><th className="p-4">Chunks</th><th className="p-4">Status</th><th className="p-4 text-right">Actions</th></tr></thead><tbody className="divide-y divide-white/5">{documents.map((doc) => <tr key={doc.id}><td className="p-4"><Link href={`/knowledge/${doc.id}`} className="font-medium text-white hover:text-cyan-300">{doc.title}</Link><p className="mt-1 font-mono text-[11px] text-slate-500">{doc.source_uri}</p></td><td className="p-4 font-mono text-slate-300">v{doc.version}</td><td className="p-4 font-mono text-slate-300">{doc.chunk_count}</td><td className="p-4"><span className={`rounded px-2 py-1 text-[10px] uppercase ${doc.status === 'active' ? 'bg-emerald-950 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>{doc.status}</span></td><td className="p-4 text-right space-x-2"><button onClick={() => act(doc.id, 'reindex')} className="text-xs text-cyan-300 hover:text-cyan-200">Reindex</button>{doc.status === 'active' && <button onClick={() => act(doc.id, 'archive')} className="text-xs text-rose-300 hover:text-rose-200">Archive</button>}</td></tr>)}</tbody></table>{documents.length === 0 && <p className="p-8 text-center text-sm text-slate-500">No knowledge documents indexed.</p>}</div>
  </div>;
}
