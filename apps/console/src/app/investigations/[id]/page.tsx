'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiFetch } from '@/lib/api';

export default function InvestigationPage() {
  const id = useParams().id as string;
  const [state, setState] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { apiFetch<Record<string, unknown>>(`investigations/${id}`).then(setState).catch((e: Error) => setError(e.message)); }, [id]);
  return <div className="space-y-6"><header><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Durable agent state</p><h1 className="mt-2 text-3xl font-semibold text-white">Investigation</h1><p className="mt-2 font-mono text-xs text-slate-500">{id}</p></header>{error && <p className="rounded-lg border border-rose-900 p-4 text-rose-300">{error}</p>}{state && <pre className="overflow-auto rounded-xl border border-white/10 bg-slate-900/45 p-5 text-xs leading-6 text-slate-300">{JSON.stringify(state, null, 2)}</pre>}</div>;
}
