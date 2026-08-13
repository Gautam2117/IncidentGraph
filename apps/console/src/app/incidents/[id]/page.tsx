'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiFetch, fetchIncidentDetail, fetchIncidentTimeline, Incident, IncidentEvent } from '@/lib/api';

export default function IncidentDetailPage() {
  const params = useParams();
  const incidentId = params?.id as string;

  const [incident, setIncident] = useState<Incident | null>(null);
  const [timeline, setTimeline] = useState<IncidentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [investigation, setInvestigation] = useState<Record<string, unknown> | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!incidentId) return;
    async function load() {
      try {
        setLoading(true);
        const [incData, timeData] = await Promise.all([
          fetchIncidentDetail(incidentId),
          fetchIncidentTimeline(incidentId),
        ]);
        setIncident(incData);
        setTimeline(timeData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load incident detail');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [incidentId]);

  async function investigate() {
    setRunning(true); setError(null);
    try { setInvestigation(await apiFetch<Record<string, unknown>>('investigations/trigger', { method: 'POST', body: JSON.stringify({ incident_id: incidentId }) })); const events = await fetchIncidentTimeline(incidentId); setTimeline(events); }
    catch (err) { setError(err instanceof Error ? err.message : 'Investigation failed'); }
    finally { setRunning(false); }
  }

  if (loading) {
    return <div className="p-8 border border-slate-800 rounded-lg text-slate-400 text-sm">Loading incident details...</div>;
  }

  if (error || !incident) {
    return <div className="p-4 border border-rose-900/50 bg-rose-950/20 text-rose-400 rounded-lg text-sm">{error || 'Incident not found'}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-4 flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">{incident.id}</span>
            <span className={`text-xs px-2 py-0.5 rounded uppercase font-semibold ${
              incident.severity === 'critical' ? 'bg-rose-950 text-rose-400 border border-rose-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
            }`}>{incident.severity}</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-2">{incident.title}</h1>
          <p className="text-sm text-slate-400 mt-1">{incident.summary || 'No summary provided'}</p>
        </div>
        <div className="flex gap-2"><button onClick={investigate} disabled={running} className="rounded-lg bg-cyan-400 px-3 py-2 text-xs font-semibold text-slate-950 disabled:opacity-50">{running ? 'Investigating…' : 'Run investigation'}</button><Link href={`/incidents/${incident.id}/postmortem`} className="rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300">Postmortem</Link></div>
      </div>

      {investigation && <div className="rounded-xl border border-cyan-900 bg-cyan-950/20 p-4"><p className="text-xs uppercase tracking-wider text-cyan-300">Investigation completed</p><pre className="mt-3 overflow-auto text-xs text-slate-400">{JSON.stringify(investigation, null, 2)}</pre></div>}

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white">Incident Event Timeline</h2>
        <div className="border border-slate-800 rounded-lg bg-slate-900/40 p-4 space-y-4">
          {timeline.length === 0 ? (
            <div className="text-sm text-slate-500">No events recorded for this incident yet.</div>
          ) : (
            timeline.map((evt) => (
              <div key={evt.id} className="flex items-start gap-4 border-b border-slate-800/60 pb-3 last:border-b-0 last:pb-0">
                <span className="text-xs font-mono text-slate-500 w-24 pt-0.5">{new Date(evt.created_at).toLocaleTimeString()}</span>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 uppercase">{evt.event_type}</span>
                    <span className="text-sm font-semibold text-slate-200">{evt.title}</span>
                  </div>
                  <pre className="text-xs font-mono bg-slate-950 p-2 rounded text-slate-400 overflow-x-auto max-w-3xl">
                    {JSON.stringify(evt.payload, null, 2)}
                  </pre>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
