'use client';

import { useEffect, useMemo, useState } from 'react';
import { EvaluationSummary, fetchEvaluations } from '@/lib/api';

export default function EvaluationsComparePage() {
  const [runs, setRuns] = useState<EvaluationSummary[]>([]);
  const [leftId, setLeftId] = useState('');
  const [rightId, setRightId] = useState('');
  useEffect(() => { fetchEvaluations().then((items) => { setRuns(items); setLeftId(items[1]?.eval_id || items[0]?.eval_id || ''); setRightId(items[0]?.eval_id || ''); }).catch(() => undefined); }, []);
  const left = useMemo(() => runs.find((run) => run.eval_id === leftId), [leftId, runs]);
  const right = useMemo(() => runs.find((run) => run.eval_id === rightId), [rightId, runs]);
  const metrics: Array<[string, keyof EvaluationSummary]> = [['Pass rate', 'overall_pass_rate'], ['Root cause accuracy', 'root_cause_accuracy'], ['Evidence recall', 'mean_causal_chain_recall'], ['Unsupported claims', 'mean_unsupported_claim_rate'], ['P95 latency', 'p95_latency_seconds']];
  return <div className="space-y-6"><header><p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Regression analysis</p><h1 className="mt-2 text-3xl font-semibold text-white">Compare evaluations</h1><p className="mt-2 text-sm text-slate-400">Persisted summaries remain explicitly separated by live and offline benchmark mode.</p></header><div className="grid md:grid-cols-2 gap-3">{[[leftId, setLeftId], [rightId, setRightId]].map(([value, setter], index) => <select key={index} value={value as string} onChange={(e) => (setter as (id: string) => void)(e.target.value)} className="rounded-lg border border-white/10 bg-slate-950 px-3 py-2 text-sm">{runs.map((run) => <option key={run.eval_id} value={run.eval_id}>{run.eval_id} · {run.benchmark_mode}</option>)}</select>)}</div>{left && right ? <div className="overflow-hidden rounded-xl border border-white/10"><table className="w-full text-sm"><thead className="bg-white/[0.03]"><tr><th className="p-4 text-left text-slate-500">Metric</th><th className="p-4 text-right font-mono text-cyan-300">{left.eval_id}</th><th className="p-4 text-right font-mono text-cyan-300">{right.eval_id}</th></tr></thead><tbody className="divide-y divide-white/5">{metrics.map(([label, key]) => { const a = Number(left[key]); const b = Number(right[key]); return <tr key={label}><td className="p-4 text-slate-300">{label}</td><td className="p-4 text-right font-mono">{a.toFixed(4)}</td><td className="p-4 text-right font-mono">{b.toFixed(4)} <span className={b - a >= 0 ? 'text-emerald-300' : 'text-rose-300'}>({(b - a).toFixed(4)})</span></td></tr>; })}</tbody></table></div> : <p className="rounded-xl border border-white/10 p-8 text-center text-slate-500">At least one persisted evaluation is required.</p>}</div>;
}
