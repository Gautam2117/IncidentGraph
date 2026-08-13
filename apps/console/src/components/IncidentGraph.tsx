'use client';
import React, { useState } from 'react';
import { Network, Server, Database, Cloud } from 'lucide-react';

const SERVICES = [
  { id: 'gateway', x: 250, y: 50, icon: Cloud, type: 'edge' },
  { id: 'auth', x: 100, y: 150, icon: Server, type: 'core' },
  { id: 'orders', x: 400, y: 150, icon: Server, type: 'core' },
  { id: 'payments', x: 400, y: 250, icon: Database, type: 'db' },
  { id: 'inventory', x: 100, y: 250, icon: Database, type: 'db' },
  { id: 'notifications', x: 250, y: 350, icon: Network, type: 'edge' },
];

const CONNECTIONS = [
  { from: 'gateway', to: 'auth' },
  { from: 'gateway', to: 'orders' },
  { from: 'orders', to: 'payments' },
  { from: 'orders', to: 'inventory' },
  { from: 'orders', to: 'notifications' },
  { from: 'payments', to: 'notifications' },
];

export function IncidentGraph({ incidentId }: { incidentId: string }) {
  const [hovered, setHovered] = useState<string | null>(null);

  // In a real app, we'd fetch actual topology based on incident trace
  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 relative h-[450px] overflow-hidden flex items-center justify-center">
      <h3 className="absolute top-4 left-4 text-white font-medium flex items-center gap-2">
        <Network size={18} className="text-blue-400" />
        Topology Graph (Incident {incidentId})
      </h3>

      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        {CONNECTIONS.map(({ from, to }) => {
          const fromNode = SERVICES.find((s) => s.id === from);
          const toNode = SERVICES.find((s) => s.id === to);
          if (!fromNode || !toNode) return null;
          
          const isHighlighted = hovered === from || hovered === to;

          return (
            <line
              key={`${from}-${to}`}
              x1={fromNode.x + 24}
              y1={fromNode.y + 24}
              x2={toNode.x + 24}
              y2={toNode.y + 24}
              stroke={isHighlighted ? "#60a5fa" : "#334155"}
              strokeWidth={isHighlighted ? 3 : 2}
              className="transition-all duration-300"
            />
          );
        })}
      </svg>

      <div className="relative w-[500px] h-[400px]">
        {SERVICES.map((service) => {
          const Icon = service.icon;
          const isAffected = incidentId && (service.id === 'payments' || service.id === 'orders');
          
          return (
            <div
              key={service.id}
              className={`absolute flex flex-col items-center justify-center cursor-pointer transition-all duration-300 z-10 
                ${hovered === service.id ? 'scale-110' : 'scale-100'}`}
              style={{ left: service.x, top: service.y }}
              onMouseEnter={() => setHovered(service.id)}
              onMouseLeave={() => setHovered(null)}
            >
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg border-2 
                  ${isAffected 
                    ? 'bg-red-500/20 border-red-500 text-red-400 shadow-red-500/20' 
                    : 'bg-slate-800 border-slate-600 text-slate-300 shadow-slate-900/50'
                  }`}
              >
                <Icon size={24} />
              </div>
              <span className={`mt-2 text-xs font-semibold px-2 py-1 rounded 
                ${isAffected ? 'bg-red-500/20 text-red-300' : 'bg-slate-800 text-slate-400'}`}>
                {service.id}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
