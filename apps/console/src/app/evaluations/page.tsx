'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { EvaluationSummary, fetchLatestEvaluation, runEvaluation } from '@/lib/api';

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function EvaluationsPage() {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  useEffect(() => { fetchLatestEvaluation().then(setSummary).catch((e: Error) => setError(e.message)); }, []);
  async function run(mode: 'offline' | 'live') { setRunning(true); setError(null); try { setSummary(await runEvaluation(mode)); } catch (e) { setError(e instanceof Error ? e.message : 'Evaluation failed'); } finally { setRunning(false); } }
  return <div className="space-y-6">
    <header className="flex flex-col md:flex-row md:items-end justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Reliability measurement</p><h1 className="mt-2 text-3xl font-semibold text-white">AI evaluations</h1><p className="mt-2 text-sm text-slate-400">Offline adapter runs are labeled and excluded from live-quality claims. Live runs own fault injection and cleanup.</p></div><div className="flex gap-2"><button disabled={running} onClick={() => run('offline')} className="rounded-lg border border-white/10 px-4 py-2 text-xs text-slate-300">Run offline check</button><button disabled={running} onClick={() => run('live')} className="rounded-lg bg-cyan-400 px-4 py-2 text-xs font-semibold text-slate-950">Run live benchmark</button></div></header>
    {error && <div className="rounded-lg border border-amber-900 bg-amber-950/30 p-3 text-sm text-amber-300">{error}</div>}
    {summary ? <>
      <div className="flex items-center gap-3"><span className={`rounded-md px-2 py-1 text-[10px] font-mono uppercase ${summary.benchmark_mode === 'live' ? 'bg-emerald-950 text-emerald-300' : 'bg-amber-950 text-amber-300'}`}>{summary.benchmark_mode}</span><Link href={`/evaluations/${summary.eval_id}`} className="font-mono text-xs text-cyan-300">{summary.eval_id}</Link><span className="text-xs text-slate-500">{summary.scenario_count} scenarios</span></div>
      <div className="grid sm:grid-cols-2 xl:grid-cols-5 gap-3">{[
        ['Pass rate', pct(summary.overall_pass_rate)], ['Root cause', pct(summary.root_cause_accuracy)], ['Evidence recall', pct(summary.mean_causal_chain_recall)], ['Unsupported claims', pct(summary.mean_unsupported_claim_rate)], ['P95 latency', `${summary.p95_latency_seconds}s`],
      ].map(([label, value]) => <div key={label} className="rounded-xl border border-white/10 bg-slate-900/45 p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-white">{value}</p></div>)}</div>
      <div className="grid lg:grid-cols-2 gap-4"><div className="rounded-xl border border-white/10 bg-slate-900/45 p-5"><h2 className="font-semibold text-white">Evidence and tool quality</h2><dl className="mt-4 space-y-3 text-sm">{[['Causal precision', pct(summary.mean_causal_chain_precision)], ['Tool choice accuracy', pct(summary.mean_tool_choice_accuracy)], ['Parameter accuracy', pct(summary.mean_tool_parameter_accuracy)], ['Safe uncertainty', pct(summary.safe_uncertainty_rate)]].map(([k, v]) => <div key={k} className="flex justify-between border-b border-white/5 pb-3"><dt className="text-slate-400">{k}</dt><dd className="font-mono text-cyan-300">{v}</dd></div>)}</dl></div><div className="rounded-xl border border-white/10 bg-slate-900/45 p-5"><h2 className="font-semibold text-white">Runtime envelope</h2><dl className="mt-4 space-y-3 text-sm">{[['P50 latency', `${summary.p50_latency_seconds}s`], ['Mean latency', `${summary.mean_latency_seconds}s`], ['Tokens', summary.total_tokens.toLocaleString()], ['Cost', `$${summary.total_cost_usd.toFixed(4)}`]].map(([k, v]) => <div key={k} className="flex justify-between border-b border-white/5 pb-3"><dt className="text-slate-400">{k}</dt><dd className="font-mono text-slate-200">{v}</dd></div>)}</dl></div></div>
    </> : <div className="rounded-xl border border-white/10 p-8 text-center text-sm text-slate-500">No completed evaluation is available.</div>}
  </div>;
}
