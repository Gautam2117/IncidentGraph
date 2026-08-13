'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const response = await fetch('/api/session/login', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setError(body.message || body.detail || 'Sign-in failed');
      setSubmitting(false);
      return;
    }
    const returnTo = new URLSearchParams(window.location.search).get('returnTo');
    router.replace(returnTo?.startsWith('/') ? returnTo : '/');
    router.refresh();
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-[1.15fr_0.85fr] bg-[#070a0f]">
      <section className="hidden lg:flex p-14 flex-col justify-between border-r border-white/10 ig-grid-bg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-400 text-slate-950 font-black grid place-items-center">IG</div>
          <span className="text-lg font-semibold">IncidentGraph</span>
        </div>
        <div className="max-w-2xl">
          <p className="text-xs uppercase tracking-[0.28em] text-cyan-300 mb-5">AI reliability control plane</p>
          <h1 className="text-5xl font-semibold tracking-[-0.04em] leading-[1.05] text-white">
            Evidence before action. Approval before change.
          </h1>
          <p className="mt-6 text-slate-400 text-lg max-w-xl">
            Investigate distributed incidents across metrics, logs, traces, deployments, and runbooks—then execute only bounded, verified remediations.
          </p>
        </div>
        <p className="text-xs text-slate-600 font-mono">POSTGRES · LANGGRAPH · OTEL · TEMPO · LOKI</p>
      </section>
      <section className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900/60 p-8 shadow-2xl">
          <p className="text-xs uppercase tracking-[0.22em] text-cyan-300">Secure console</p>
          <h2 className="mt-3 text-3xl font-semibold text-white">Sign in</h2>
          <p className="mt-2 text-sm text-slate-400">Use an active IncidentGraph account.</p>
          <label className="block mt-8 text-sm text-slate-300">
            Username or email
            <input autoComplete="username" required value={username} onChange={(e) => setUsername(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 outline-none focus:border-cyan-400" />
          </label>
          <label className="block mt-4 text-sm text-slate-300">
            Password
            <input type="password" autoComplete="current-password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 outline-none focus:border-cyan-400" />
          </label>
          {error && <p role="alert" className="mt-4 rounded-lg border border-rose-800 bg-rose-950/40 px-3 py-2 text-sm text-rose-300">{error}</p>}
          <button disabled={submitting} className="mt-6 w-full rounded-lg bg-cyan-400 px-4 py-2.5 font-semibold text-slate-950 hover:bg-cyan-300 disabled:opacity-60">
            {submitting ? 'Signing in…' : 'Open control plane'}
          </button>
        </form>
      </section>
    </div>
  );
}
