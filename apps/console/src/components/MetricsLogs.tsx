'use client';
import React, { useState } from 'react';
import { Activity, Terminal } from 'lucide-react';

export function MetricsLogs() {
  const [activeTab, setActiveTab] = useState<'logs' | 'metrics'>('logs');

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 flex flex-col overflow-hidden h-[450px]">
      <div className="flex border-b border-slate-800 bg-slate-900/50">
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex-1 py-3 px-4 flex items-center justify-center gap-2 font-medium text-sm transition-colors ${
            activeTab === 'logs' ? 'bg-slate-800 text-white border-b-2 border-blue-500' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Terminal size={16} />
          Loki Error Logs
        </button>
        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex-1 py-3 px-4 flex items-center justify-center gap-2 font-medium text-sm transition-colors ${
            activeTab === 'metrics' ? 'bg-slate-800 text-white border-b-2 border-blue-500' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity size={16} />
          Prometheus Metrics
        </button>
      </div>

      <div className="flex-1 p-4 bg-slate-950 font-mono text-xs overflow-y-auto">
        {activeTab === 'logs' ? (
          <div className="space-y-2">
            <div className="text-slate-400">[2024-03-20 14:32:01] <span className="text-blue-400">INFO</span> payments-svc: Processing transaction txn_8921</div>
            <div className="text-slate-400">[2024-03-20 14:32:05] <span className="text-yellow-400">WARN</span> payments-svc: Connection to db slowing down (1500ms)</div>
            <div className="text-slate-400">[2024-03-20 14:32:10] <span className="text-red-400 font-bold">ERROR</span> payments-svc: ConnectionTimeoutError: failed to acquire lock on payments_db</div>
            <div className="text-slate-400">[2024-03-20 14:32:10] <span className="text-red-400 font-bold">ERROR</span> orders-svc: 500 Internal Server Error from downstream payments-svc</div>
            <div className="text-slate-400">[2024-03-20 14:32:15] <span className="text-red-400 font-bold">ERROR</span> payments-svc: ConnectionTimeoutError: failed to acquire lock on payments_db</div>
            <div className="text-slate-400">[2024-03-20 14:32:15] <span className="text-red-400 font-bold">ERROR</span> orders-svc: 500 Internal Server Error from downstream payments-svc</div>
            <div className="animate-pulse text-slate-500 mt-4">Waiting for new logs...</div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <div className="text-slate-400 mb-1">payments-svc CPU Usage</div>
              <div className="h-24 flex items-end gap-1 opacity-80">
                {[40,45,42,48,50,55,60,85,95,98,99,99,99].map((val, i) => (
                  <div key={i} className={`flex-1 rounded-t-sm ${val > 90 ? 'bg-red-500' : val > 70 ? 'bg-yellow-500' : 'bg-blue-500'}`} style={{ height: `${val}%` }} />
                ))}
              </div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">orders-svc HTTP 5xx Rate</div>
              <div className="h-24 flex items-end gap-1 opacity-80">
                {[0,0,0,0,0,2,5,15,45,80,95,98,99].map((val, i) => (
                  <div key={i} className={`flex-1 rounded-t-sm ${val > 50 ? 'bg-red-500' : val > 10 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ height: `${val}%` }} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
