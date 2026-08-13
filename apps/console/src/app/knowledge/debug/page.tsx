'use client';

import { FormEvent, useState } from 'react';
import { KnowledgeSearchResult, searchKnowledge } from '@/lib/api';

export default function KnowledgeDebugPage() {
  const [query, setQuery] = useState('connection pool saturation timeout');
  const [mode, setMode] = useState<'vector' | 'lexical' | 'hybrid'>('hybrid');
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  async function submit(event: FormEvent) { event.preventDefault(); setError(null); try { setResults(await searchKnowledge(query, mode)); } catch (e) { setError(e instanceof Error ? e.message : 'Search failed'); } }
  return <div className="space-y-6"><header><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Retrieval debugger</p><h1 className="mt-2 text-3xl font-semibold text-white">Inspect ranked evidence</h1><p className="mt-2 text-sm text-slate-400">Compare vector, lexical, and reciprocal-rank-fused retrieval over active document versions.</p></header><form onSubmit={submit} className="flex flex-col md:flex-row gap-2"><input value={query} onChange={(e) => setQuery(e.target.value)} required minLength={2} className="flex-1 rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm" /><select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)} className="rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm"><option value="hybrid">Hybrid RRF</option><option value="vector">Vector</option><option value="lexical">Lexical</option></select><button className="rounded-lg bg-cyan-400 px-4 py-2 text-xs font-semibold text-slate-950">Search</button></form>{error && <p className="text-rose-300">{error}</p>}<div className="space-y-3">{results.map((result, index) => <article key={result.chunk_id} className="rounded-xl border border-white/10 bg-slate-900/45 p-5"><div className="flex justify-between text-xs"><span className="font-mono text-cyan-300">#{index + 1} · {result.document_id}</span><span className="font-mono text-slate-500">{result.score.toFixed(6)}</span></div><p className="mt-3 text-sm leading-6 text-slate-300">{result.content}</p></article>)}</div></div>;
}
