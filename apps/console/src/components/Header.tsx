'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

type Profile = { email: string; role: string; username: string };

export default function Header() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  useEffect(() => {
    const handleUnauthorized = () => {
      router.push(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`);
    };
    window.addEventListener('incidentgraph:unauthorized', handleUnauthorized);
    apiFetch<Profile>('auth/me').then(setProfile).catch(() => undefined);
    return () => window.removeEventListener('incidentgraph:unauthorized', handleUnauthorized);
  }, [router]);

  async function logout() {
    await fetch('/api/session/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  }

  return (
    <header className="h-16 border-b border-white/10 bg-[#080c12]/95 backdrop-blur px-4 md:px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-cyan-400 text-slate-950 grid place-items-center font-black text-sm">IG</div>
        <div>
          <span className="font-semibold text-white tracking-tight">IncidentGraph</span>
          <span className="hidden sm:inline ml-3 text-[10px] text-slate-500 font-mono uppercase tracking-widest">Reliability control plane</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="text-slate-400">Authenticated</span>
          <span className="text-slate-200">{profile?.email || 'Loading…'}</span>
        </div>
        <span className="rounded-md border border-cyan-900 bg-cyan-950/50 px-2 py-1 text-[10px] font-mono uppercase text-cyan-300">{profile?.role || '—'}</span>
        <button onClick={logout} className="text-xs text-slate-400 hover:text-white">Sign out</button>
      </div>
    </header>
  );
}
