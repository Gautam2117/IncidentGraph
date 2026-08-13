'use client';

import { useEffect, useState } from 'react';
import { fetchTopology, TopologyGraph } from '@/lib/api';

export default function TopologyPage() {
  const [topology, setTopology] = useState<TopologyGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchTopology();
        setTopology(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load topology');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Service Dependency Topology</h1>
        <p className="text-sm text-slate-400 mt-1">Live architecture topology extracted from OpenTelemetry trace context propagation</p>
      </div>

      {loading ? (
        <div className="p-8 border border-slate-800 rounded-lg text-slate-400 text-sm">Loading service graph...</div>
      ) : error ? (
        <div className="p-4 border border-rose-900/50 bg-rose-950/20 text-rose-400 rounded-lg text-sm">{error}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border border-slate-800 bg-slate-900/40 p-5 rounded-lg space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Service Nodes ({topology?.nodes.length})</h2>
            <div className="space-y-2 font-mono text-xs">
              {topology?.nodes.map((node) => (
                <div key={node.id} className="p-3 border border-slate-800 rounded bg-slate-900/80 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`h-2.5 w-2.5 rounded-full ${node.type === 'database' ? 'bg-amber-400' : node.type === 'cache' ? 'bg-purple-400' : 'bg-emerald-400'}`} />
                    <span className="font-semibold text-slate-200">{node.name}</span>
                  </div>
                  <span className="text-slate-500 uppercase">{node.type}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-slate-800 bg-slate-900/40 p-5 rounded-lg space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Dependency Relationships ({topology?.edges.length})</h2>
            <div className="space-y-2 font-mono text-xs">
              {topology?.edges.map((edge, idx) => (
                <div key={idx} className="p-3 border border-slate-800 rounded bg-slate-900/80 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-400 font-semibold">{edge.source}</span>
                    <span className="text-slate-500">→</span>
                    <span className="text-cyan-400 font-semibold">{edge.target}</span>
                  </div>
                  <span className="text-slate-400 text-2xs">{edge.description || edge.protocol}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
