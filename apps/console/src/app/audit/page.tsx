'use client';

import { useEffect, useState } from 'react';
import { AuditEvent, fetchAuditEvents } from '@/lib/api';

export default function AuditTrailPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetchAuditEvents().then(setEvents).catch((e: Error) => setError(e.message)); }, []);
  return <div className="space-y-6"><header><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Security ledger</p><h1 className="mt-2 text-3xl font-semibold text-white">Audit trail</h1><p className="mt-2 text-sm text-slate-400">Admin-only record of authentication, tool use, knowledge mutations, approvals, and controlled actions.</p></header>{error && <div className="rounded-lg border border-amber-900 bg-amber-950/30 p-3 text-sm text-amber-300">{error}</div>}<div className="space-y-2">{events.map((event) => <article key={event.id} className="grid md:grid-cols-[170px_1fr_220px] gap-3 rounded-lg border border-white/10 bg-slate-900/40 p-4 text-xs"><time className="font-mono text-slate-500">{new Date(event.created_at).toLocaleString()}</time><div><p className="font-semibold text-white">{event.action}</p><p className="mt-1 text-slate-500">{event.resource_type} · {event.resource_id}</p></div><div className="text-right"><p className="text-cyan-300">{event.actor}</p><details className="mt-1 text-slate-500"><summary className="cursor-pointer">details</summary><pre className="mt-2 overflow-auto text-left">{JSON.stringify(event.details, null, 2)}</pre></details></div></article>)}{!events.length && !error && <p className="rounded-xl border border-white/10 p-8 text-center text-slate-500">No audit events found.</p>}</div></div>;
}
