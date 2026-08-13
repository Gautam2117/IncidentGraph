'use client';
import React from 'react';
import { CheckCircle, Circle, PlayCircle, Loader2 } from 'lucide-react';

const STEPS = [
  { id: 'triage', label: 'Triage Incident', status: 'completed' },
  { id: 'query_logs', label: 'Query Loki Logs', status: 'completed' },
  { id: 'query_metrics', label: 'Query Prometheus', status: 'completed' },
  { id: 'rca', label: 'Synthesize RCA', status: 'in-progress' },
  { id: 'remediate', label: 'Generate Remediation', status: 'pending' },
  { id: 'human', label: 'HITL Approval', status: 'pending' },
  { id: 'execute', label: 'Execute Sandbox', status: 'pending' },
];

export function LangGraphSteps() {
  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
      <h3 className="text-white font-medium mb-6">LangGraph Execution</h3>
      
      <div className="space-y-4">
        {STEPS.map((step, idx) => {
          const isCompleted = step.status === 'completed';
          const isInProgress = step.status === 'in-progress';
          const isPending = step.status === 'pending';

          return (
            <div key={step.id} className="flex items-start gap-4">
              <div className="relative flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center 
                  ${isCompleted ? 'bg-green-500/20 text-green-400' : 
                    isInProgress ? 'bg-blue-500/20 text-blue-400' : 
                    'bg-slate-800 text-slate-500'}`}>
                  {isCompleted ? <CheckCircle size={18} /> : 
                   isInProgress ? <Loader2 size={18} className="animate-spin" /> :
                   <Circle size={18} />}
                </div>
                {idx < STEPS.length - 1 && (
                  <div className={`w-0.5 h-6 my-1 ${isCompleted ? 'bg-green-500/50' : 'bg-slate-800'}`} />
                )}
              </div>
              
              <div className="pt-1 flex-1">
                <p className={`font-medium ${isCompleted ? 'text-green-400' : isInProgress ? 'text-blue-400' : 'text-slate-500'}`}>
                  {step.label}
                </p>
                {isInProgress && (
                  <div className="mt-2 text-xs bg-slate-800 rounded p-2 text-slate-300 font-mono flex items-center gap-2">
                    <PlayCircle size={14} className="text-blue-400" />
                    Executing node: {step.id}...
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
