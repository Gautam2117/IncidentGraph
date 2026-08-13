'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiFetch } from '@/lib/api';

type Postmortem = { markdown_content: string; title?: string };

export default function PostmortemPage() {
  const incidentId = useParams().id as string;
  const [report, setReport] = useState<Postmortem | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => { void apiFetch<Postmortem>(`postmortems/${incidentId}`).then(setReport).catch(() => setReport(null)); }, [incidentId]);
  async function generate() { setMessage('Generating and indexing postmortem…'); try { setReport(await apiFetch<Postmortem>('postmortems/generate', { method: 'POST', body: JSON.stringify({ incident_id: incidentId }) })); setMessage(null); } catch (e) { setMessage(e instanceof Error ? e.message : 'Generation failed'); } }
  return <div className="space-y-6"><header className="flex justify-between gap-4"><div><p className="font-mono text-xs text-cyan-300">{incidentId}</p><h1 className="mt-2 text-3xl font-semibold text-white">Incident postmortem</h1><p className="mt-2 text-sm text-slate-400">Generated from persisted investigation evidence and indexed back into the knowledge corpus.</p></div><button onClick={generate} className="h-fit rounded-lg bg-cyan-400 px-4 py-2 text-xs font-semibold text-slate-950">Generate report</button></header>{message && <div className="rounded-lg border border-amber-900 p-3 text-sm text-amber-300">{message}</div>}<div className="rounded-xl border border-white/10 bg-slate-900/40 p-6"><pre className="whitespace-pre-wrap font-sans text-sm leading-7 text-slate-300">{report?.markdown_content || 'No postmortem has been generated for this incident.'}</pre></div></div>;
}
