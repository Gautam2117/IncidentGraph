'use client';
import React from 'react';
import { AlertTriangle, TerminalSquare } from 'lucide-react';

export function PlaywrightStatus() {
  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
      <h3 className="text-white font-medium mb-4 flex items-center gap-2">
        <TerminalSquare size={18} className="text-indigo-400" />
        Sandbox Remediation Execution
      </h3>

      <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm">
        <div className="flex items-center gap-2 text-yellow-500 mb-2 font-medium">
          <AlertTriangle size={16} />
          <span>DRY RUN MODE ENABLED</span>
        </div>
        
        <div className="space-y-1 text-slate-400">
          <div>$ kubectl rollout restart deployment/demo-payments -n default</div>
          <div className="text-green-400">deployment.apps/demo-payments restarted</div>
          
          <div className="mt-4">$ kubectl get pods -l app=demo-payments -w</div>
          <div className="text-slate-500">demo-payments-7f8d... 0/1 Terminating</div>
          <div className="text-slate-500">demo-payments-8a2b... 0/1 ContainerCreating</div>
          <div className="text-green-400">demo-payments-8a2b... 1/1 Running</div>
        </div>
      </div>
      
      <div className="mt-4 flex gap-3">
        <button className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg font-medium transition-colors">
          Approve & Execute
        </button>
        <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded-lg font-medium transition-colors">
          Reject
        </button>
      </div>
    </div>
  );
}
