'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { fetchKnowledgeDocument, KnowledgeDocument } from '@/lib/api';

export default function KnowledgeDocPage() {
  const id = useParams().id as string;
  const [doc, setDoc] = useState<KnowledgeDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetchKnowledgeDocument(id).then(setDoc).catch((e: Error) => setError(e.message)); }, [id]);
  if (error) return <div className="rounded-lg border border-rose-900 p-4 text-rose-300">{error}</div>;
  if (!doc) return <div className="text-slate-500">Loading document…</div>;
  return <article className="max-w-4xl space-y-6"><header><p className="font-mono text-xs text-cyan-300">{doc.source_uri}</p><h1 className="mt-2 text-3xl font-semibold text-white">{doc.title}</h1><div className="mt-3 flex gap-2 text-xs text-slate-400"><span>v{doc.version}</span><span>·</span><span>{doc.chunk_count} chunks</span><span>·</span><span>{doc.status}</span></div></header><div className="whitespace-pre-wrap rounded-xl border border-white/10 bg-slate-900/40 p-6 leading-7 text-slate-300">{doc.content}</div></article>;
}
