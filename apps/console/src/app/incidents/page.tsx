'use client';

import { useEffect, useState } from 'react';
import { fetchIncidents, Incident } from '@/lib/api';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchIncidents();
        setIncidents(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load incidents');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Active & Historical Incidents</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time incident ingestion, telemetry correlation, and lifecycle tracking</p>
        </div>
      </div>

      {loading ? (
        <div className="p-8 border border-slate-800 rounded-lg bg-slate-900/50 text-slate-400 text-sm">
          Loading active incidents...
        </div>
      ) : error ? (
        <div className="p-4 border border-rose-900/50 bg-rose-950/20 text-rose-400 rounded-lg text-sm">
          {error}
        </div>
      ) : incidents.length === 0 ? (
        <div className="p-12 border border-slate-800 rounded-lg bg-slate-900/30 text-center space-y-3">
          <div className="text-slate-400 text-sm">No open incidents in the current workspace</div>
          <p className="text-xs text-slate-500">Trigger a scenario or send an alert webhook to open an incident.</p>
        </div>
      ) : (
        <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/40">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <th className="p-4">Incident ID</th>
                <th className="p-4">Title</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Status</th>
                <th className="p-4">Target Service</th>
                <th className="p-4">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {incidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 text-emerald-400 font-semibold">
                    <a href={`/incidents/${inc.id}`} className="hover:underline">{inc.id}</a>
                  </td>
                  <td className="p-4 text-slate-200 font-sans text-sm font-medium">{inc.title}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded font-semibold uppercase tracking-wider ${
                      inc.severity === 'critical' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                      inc.severity === 'high' ? 'bg-orange-950 text-orange-400 border border-orange-800' :
                      inc.severity === 'medium' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                      {inc.status}
                    </span>
                  </td>
                  <td className="p-4 text-slate-300">{inc.target_service || 'N/A'}</td>
                  <td className="p-4 text-slate-400">{new Date(inc.created_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
