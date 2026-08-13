'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { fetchScenarioRun, ScenarioRun } from '@/lib/api';

export default function ScenarioRunDetailsPage() {
  const id = useParams().id as string;
  const [run, setRun] = useState<ScenarioRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetchScenarioRun(id).then(setRun).catch((e: Error) => setError(e.message)); }, [id]);
  return <div className="space-y-6"><header><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Fault execution</p><h1 className="mt-2 text-3xl font-semibold text-white">Scenario run</h1><p className="mt-2 font-mono text-xs text-slate-500">{id}</p></header>{error && <p className="rounded-lg border border-amber-900 p-4 text-amber-300">{error}</p>}{run && <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-3">{[['State', run.state], ['Fault acknowledged', run.fault_ack ? 'yes' : 'no'], ['Probe status', run.probe_status_code?.toString() || '—'], ['Probe latency', run.probe_latency_ms ? `${run.probe_latency_ms}ms` : '—']].map(([label, value]) => <div key={label} className="rounded-xl border border-white/10 bg-slate-900/45 p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 font-mono text-lg text-white">{value}</p></div>)}</div>}</div>;
}
