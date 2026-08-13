'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { fetchHealthReady, fetchIncidents, fetchLatestEvaluation, fetchScenarios, Incident } from '@/lib/api';

export default function RootDashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [scenarioCount, setScenarioCount] = useState<number | null>(null);
  const [readiness, setReadiness] = useState('checking');
  const [passRate, setPassRate] = useState<string>('—');
  useEffect(() => {
    fetchIncidents().then(setIncidents).catch(() => undefined);
    fetchScenarios().then((items) => setScenarioCount(items.length)).catch(() => undefined);
    fetchHealthReady().then((value) => setReadiness(value.status)).catch(() => setReadiness('unhealthy'));
    fetchLatestEvaluation().then((value) => setPassRate(`${(value.overall_pass_rate * 100).toFixed(1)}% ${value.benchmark_mode}`)).catch(() => undefined);
  }, []);
  const active = incidents.filter((incident) => !['resolved', 'closed'].includes(incident.status));
  const critical = active.filter((incident) => incident.severity === 'critical').length;
  return <div className="space-y-6">
    <section className="relative overflow-hidden rounded-2xl border border-cyan-400/15 bg-slate-900/50 p-6 md:p-8 ig-grid-bg"><div className="relative max-w-3xl"><p className="text-xs uppercase tracking-[0.22em] text-cyan-300">Operational overview</p><h1 className="mt-3 text-3xl md:text-4xl font-semibold tracking-[-0.035em] text-white">Investigate with evidence. Remediate with control.</h1><p className="mt-4 text-slate-400 max-w-2xl">IncidentGraph correlates live telemetry and versioned runbooks, challenges its own hypotheses, and pauses every consequential change at an auditable human gate.</p><div className="mt-6 flex flex-wrap gap-2"><Link href="/incidents" className="rounded-lg bg-cyan-400 px-4 py-2 text-xs font-semibold text-slate-950">Open incident queue</Link><Link href="/scenarios" className="rounded-lg border border-white/10 bg-slate-950/60 px-4 py-2 text-xs text-slate-300">Enter chaos lab</Link></div></div></section>
    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">{[['Active incidents', active.length.toString(), critical ? `${critical} critical` : 'No critical incidents'], ['Platform readiness', readiness, 'PostgreSQL + Redis'], ['Scenario catalog', scenarioCount?.toString() || '—', 'Safe metadata only'], ['Latest benchmark', passRate, 'Mode explicitly labeled']].map(([label, value, note]) => <div key={label} className="rounded-xl border border-white/10 bg-slate-900/45 p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-white capitalize">{value}</p><p className="mt-1 text-[11px] text-cyan-300">{note}</p></div>)}</div>
    <div className="grid xl:grid-cols-[1.3fr_0.7fr] gap-4"><section className="rounded-xl border border-white/10 bg-slate-900/45 p-5"><div className="flex justify-between"><h2 className="font-semibold text-white">Incident queue</h2><Link href="/incidents" className="text-xs text-cyan-300">View all</Link></div><div className="mt-4 space-y-2">{active.slice(0, 5).map((incident) => <Link href={`/incidents/${incident.id}`} key={incident.id} className="grid grid-cols-[1fr_auto] gap-3 rounded-lg border border-white/5 bg-slate-950/60 p-3 hover:border-cyan-400/20"><div><p className="text-sm font-medium text-white">{incident.title}</p><p className="mt-1 text-xs text-slate-500">{incident.target_service || 'unscoped'} · {incident.status}</p></div><span className={`text-[10px] uppercase ${incident.severity === 'critical' ? 'text-rose-300' : 'text-amber-300'}`}>{incident.severity}</span></Link>)}{!active.length && <p className="py-8 text-center text-sm text-slate-500">No active incidents.</p>}</div></section><section className="rounded-xl border border-white/10 bg-slate-900/45 p-5"><h2 className="font-semibold text-white">Investigation path</h2><ol className="mt-4 space-y-3 text-sm">{['Scope incident and service', 'Collect metrics, logs, and traces', 'Retrieve versioned knowledge', 'Generate and challenge hypotheses', 'Synthesize supported RCA', 'Gate, execute, and verify remediation'].map((step, index) => <li key={step} className="flex gap-3"><span className="w-6 h-6 shrink-0 rounded-full border border-cyan-400/30 text-cyan-300 grid place-items-center text-[10px]">{index + 1}</span><span className="pt-0.5 text-slate-400">{step}</span></li>)}</ol></section></div>
  </div>;
}
