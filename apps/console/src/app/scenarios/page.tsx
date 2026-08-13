'use client';

import { useEffect, useMemo, useState } from 'react';
import { fetchScenarios, resetScenario, Scenario, ScenarioRun, triggerScenario } from '@/lib/api';

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [query, setQuery] = useState('');
  const [runs, setRuns] = useState<Record<string, ScenarioRun>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetchScenarios().then(setScenarios).catch((e: Error) => setError(e.message)); }, []);
  const filtered = useMemo(() => scenarios.filter((item) => `${item.id} ${item.title} ${item.category} ${item.target_service}`.toLowerCase().includes(query.toLowerCase())), [query, scenarios]);

  async function action(id: string, kind: 'trigger' | 'reset') {
    setBusy(id); setError(null);
    try { const run = kind === 'trigger' ? await triggerScenario(id) : await resetScenario(id); setRuns((current) => ({ ...current, [id]: run })); }
    catch (e) { setError(e instanceof Error ? e.message : 'Scenario action failed'); }
    finally { setBusy(null); }
  }

  return <div className="space-y-6">
    <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Controlled fault lab</p><h1 className="mt-2 text-3xl font-semibold text-white">Chaos scenarios</h1><p className="mt-2 text-sm text-slate-400">All {scenarios.length || 36} scenarios expose safe metadata only. Ground truth remains isolated from the agent.</p></div>
      <input aria-label="Filter scenarios" placeholder="Filter service, category, scenario…" value={query} onChange={(e) => setQuery(e.target.value)} className="w-full md:w-80 rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400" />
    </header>
    {error && <div className="rounded-lg border border-rose-900 bg-rose-950/30 p-3 text-sm text-rose-300">{error}</div>}
    <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
      {filtered.map((item) => <article key={item.id} className="rounded-xl border border-white/10 bg-slate-900/45 p-5 flex flex-col">
        <div className="flex items-start justify-between gap-3"><div><p className="font-mono text-xs text-cyan-300">{item.id}</p><h2 className="mt-2 font-semibold text-white">{item.title}</h2></div><span className="rounded-md bg-slate-800 px-2 py-1 text-[10px] uppercase text-slate-400">{item.category}</span></div>
        <p className="mt-3 text-sm text-slate-400 flex-1">{item.summary}</p>
        <div className="mt-4 flex flex-wrap gap-2 text-[11px]"><span className="rounded bg-cyan-950/50 px-2 py-1 text-cyan-300">target: {item.target_service}</span>{item.affected_services.slice(0, 2).map((service) => <span key={service} className="rounded bg-slate-800 px-2 py-1 text-slate-400">{service}</span>)}</div>
        {runs[item.id] && <div className="mt-4 rounded-lg border border-white/10 bg-slate-950/70 p-3 text-xs font-mono text-slate-400"><span className="text-emerald-300">{runs[item.id].state}</span>{runs[item.id].probe_status_code && ` · HTTP ${runs[item.id].probe_status_code}`}{runs[item.id].probe_latency_ms && ` · ${runs[item.id].probe_latency_ms}ms`}</div>}
        <div className="mt-4 grid grid-cols-2 gap-2"><button disabled={busy === item.id} onClick={() => action(item.id, 'trigger')} className="rounded-lg bg-cyan-400 px-3 py-2 text-xs font-semibold text-slate-950 disabled:opacity-50">Inject & probe</button><button disabled={busy === item.id} onClick={() => action(item.id, 'reset')} className="rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300 hover:bg-white/5 disabled:opacity-50">Reset baseline</button></div>
      </article>)}
    </div>
  </div>;
}
