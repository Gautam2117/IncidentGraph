'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { EvaluationSummary, fetchEvaluation } from '@/lib/api';

export default function EvaluationDetailPage() {
  const id = useParams().id as string;
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetchEvaluation(id).then(setSummary).catch((e: Error) => setError(e.message)); }, [id]);
  if (error) return <div className="rounded-lg border border-rose-900 p-4 text-rose-300">{error}</div>;
  if (!summary) return <div className="text-slate-500">Loading evaluation…</div>;
  return <div className="space-y-6"><header><p className="font-mono text-xs text-cyan-300">{summary.eval_id}</p><h1 className="mt-2 text-3xl font-semibold text-white">Scenario results</h1><p className="mt-2 text-sm text-slate-400">{summary.benchmark_mode} · {summary.scenario_count} scenarios · {(summary.overall_pass_rate * 100).toFixed(1)}% passed</p></header><div className="overflow-x-auto rounded-xl border border-white/10"><table className="w-full text-left text-xs"><thead className="bg-white/[0.03] uppercase text-slate-500"><tr><th className="p-3">Scenario</th><th className="p-3">Service</th><th className="p-3">Root cause</th><th className="p-3">Recall</th><th className="p-3">Unsupported</th><th className="p-3">Latency</th><th className="p-3">Result</th></tr></thead><tbody className="divide-y divide-white/5">{summary.metrics.map((metric) => <tr key={metric.scenario_id}><td className="p-3"><p className="font-medium text-white">{metric.scenario_title}</p><p className="mt-1 font-mono text-slate-600">{metric.scenario_id}</p></td><td className="p-3">{metric.primary_service_match ? 'match' : 'miss'}</td><td className="p-3">{metric.root_cause_match ? 'match' : 'miss'}</td><td className="p-3 font-mono">{(metric.causal_chain_recall * 100).toFixed(0)}%</td><td className="p-3 font-mono">{(metric.unsupported_claim_rate * 100).toFixed(0)}%</td><td className="p-3 font-mono">{metric.latency_seconds}s</td><td className={`p-3 font-semibold ${metric.passed ? 'text-emerald-300' : 'text-rose-300'}`}>{metric.passed ? 'PASS' : 'FAIL'}</td></tr>)}</tbody></table></div></div>;
}
