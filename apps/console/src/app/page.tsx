import Link from 'next/link';
import { ArrowRight, Braces, CheckCircle2, Code2, GitPullRequestArrow, Radar, ShieldCheck, Sparkles, Waypoints } from 'lucide-react';

const proof = [['81', 'backend tests'], ['80%', 'measured coverage'], ['168', 'requests / sec'], ['17', 'healthy containers']];

const capabilities = [
  { icon: Waypoints, eyebrow: 'Investigate', title: 'A graph that argues with itself', body: 'Durable LangGraph roles triage, collect telemetry, retrieve knowledge, challenge hypotheses, and synthesize a supported RCA.' },
  { icon: Radar, eyebrow: 'Retrieve', title: 'Evidence, ranked twice', body: 'pgvector semantic search and PostgreSQL full-text search merge through reciprocal-rank fusion over versioned operational knowledge.' },
  { icon: ShieldCheck, eyebrow: 'Remediate', title: 'Control is the product', body: 'Every action is allow-listed, schema-validated, paused for human approval, audited, and verified against post-change telemetry.' },
];

const stack = ['Next.js 16', 'FastAPI', 'LangGraph', 'PostgreSQL', 'pgvector', 'Redis', 'OpenTelemetry', 'Prometheus', 'Loki', 'Tempo', 'Kubernetes', 'Terraform'];

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#05080c] text-slate-100">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[720px] bg-[radial-gradient(circle_at_68%_18%,rgba(34,211,238,0.12),transparent_34%),radial-gradient(circle_at_25%_12%,rgba(59,130,246,0.09),transparent_28%)]" />
      <nav className="relative mx-auto flex max-w-7xl items-center justify-between px-5 py-5 md:px-8">
        <Link href="/" className="flex items-center gap-3" aria-label="IncidentGraph home"><span className="grid h-9 w-9 place-items-center rounded-xl bg-cyan-300 font-black text-slate-950 shadow-[0_0_32px_rgba(34,211,238,0.2)]">IG</span><span className="font-semibold tracking-tight text-white">IncidentGraph</span></Link>
        <div className="flex items-center gap-2">
          <a href="https://github.com/Gautam2117/IncidentGraph" target="_blank" rel="noreferrer" className="hidden items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:text-white sm:flex"><Code2 className="h-4 w-4" /> Source</a>
          <Link href="/dashboard" className="group flex items-center gap-2 rounded-lg border border-cyan-300/25 bg-cyan-300/10 px-4 py-2 text-sm font-medium text-cyan-100 transition hover:bg-cyan-300/15">Explore live showcase <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" /></Link>
        </div>
      </nav>

      <section className="relative mx-auto grid max-w-7xl gap-14 px-5 pb-20 pt-20 md:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:pb-28 lg:pt-28">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/[0.06] px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.16em] text-emerald-200"><span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_#6ee7b7]" /> Public interactive showcase</div>
          <h1 className="mt-7 max-w-3xl text-5xl font-semibold leading-[0.98] tracking-[-0.055em] text-white sm:text-6xl lg:text-7xl">Incidents explain themselves.<br /><span className="text-slate-500">Changes still need a human.</span></h1>
          <p className="mt-7 max-w-2xl text-base leading-7 text-slate-400 md:text-lg">An evidence-driven AI reliability control plane for investigating distributed failures, measuring reasoning quality, and executing only bounded, approved remediations.</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="/incidents/inc-payments-042" className="group flex items-center gap-2 rounded-xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">Trace a SEV-1 <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" /></Link>
            <a href="https://github.com/Gautam2117/IncidentGraph#architecture-overview" target="_blank" rel="noreferrer" className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm text-slate-300 transition hover:border-white/20 hover:text-white"><Braces className="h-4 w-4" /> Read the architecture</a>
          </div>
          <p className="mt-5 max-w-xl text-xs leading-5 text-slate-600">The public experience replays deterministic, clearly labeled proof data. No synthetic result is represented as a live-model benchmark.</p>
        </div>

        <div className="relative mx-auto w-full max-w-xl">
          <div className="absolute -inset-10 rounded-full bg-cyan-400/[0.05] blur-3xl" />
          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#090e15]/90 shadow-2xl shadow-black/50">
            <div className="flex h-11 items-center justify-between border-b border-white/10 px-4"><div className="flex gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-rose-400/70" /><span className="h-2.5 w-2.5 rounded-full bg-amber-300/70" /><span className="h-2.5 w-2.5 rounded-full bg-emerald-300/70" /></div><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">investigation graph · inc-042</span></div>
            <div className="ig-grid-bg p-5 sm:p-7">
              <div className="grid grid-cols-3 gap-2 text-center text-[10px] uppercase tracking-wider">{['Triage', 'Investigate', 'Skeptic'].map((node, index) => <div key={node} className={`rounded-lg border p-3 ${index === 1 ? 'border-cyan-300/40 bg-cyan-300/10 text-cyan-200' : 'border-white/10 bg-slate-950/80 text-slate-400'}`}><span className={`mx-auto mb-2 block h-1.5 w-1.5 rounded-full ${index < 2 ? 'bg-emerald-300' : 'bg-amber-300'}`} />{node}</div>)}</div>
              <div className="mx-auto h-7 w-px bg-gradient-to-b from-cyan-300/50 to-cyan-300/10" />
              <div className="rounded-xl border border-cyan-300/20 bg-slate-950/90 p-4"><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-[10px] uppercase tracking-widest text-cyan-300">supported root cause</p><p className="mt-2 text-sm font-medium leading-6 text-white">Payments pool limit regressed from 40 → 8</p></div><span className="rounded-md bg-emerald-300/10 px-2 py-1 font-mono text-[10px] text-emerald-200">0.91</span></div><div className="mt-4 grid grid-cols-3 gap-2 border-t border-white/5 pt-4 text-center"><div><p className="text-sm font-semibold text-white">18×</p><p className="mt-1 text-[9px] uppercase text-slate-600">pool wait</p></div><div><p className="text-sm font-semibold text-white">2</p><p className="mt-1 text-[9px] uppercase text-slate-600">contradictions</p></div><div><p className="text-sm font-semibold text-white">0</p><p className="mt-1 text-[9px] uppercase text-slate-600">unsupported</p></div></div></div>
              <div className="mx-auto h-7 w-px bg-gradient-to-b from-cyan-300/30 to-amber-300/30" />
              <div className="flex items-center justify-between rounded-xl border border-amber-300/20 bg-amber-300/[0.06] p-4"><div className="flex items-center gap-3"><ShieldCheck className="h-5 w-5 text-amber-200" /><div><p className="text-xs font-medium text-white">Human approval required</p><p className="mt-0.5 text-[10px] text-slate-500">bounded config rollback · canary</p></div></div><span className="rounded-md border border-amber-200/15 px-2 py-1 text-[9px] uppercase text-amber-100">paused</span></div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-white/[0.07] bg-white/[0.015]"><div className="mx-auto grid max-w-7xl grid-cols-2 px-5 md:grid-cols-4 md:px-8">{proof.map(([value, label]) => <div key={label} className="border-white/[0.07] px-4 py-7 first:border-l md:border-r"><p className="text-3xl font-semibold tracking-tight text-white">{value}</p><p className="mt-1 text-xs text-slate-500">{label}</p></div>)}</div></section>

      <section className="mx-auto max-w-7xl px-5 py-24 md:px-8 lg:py-32">
        <div className="max-w-2xl"><p className="text-xs uppercase tracking-[0.24em] text-cyan-300">Designed for the hard part</p><h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-white md:text-5xl">An AI system you can interrogate.</h2><p className="mt-5 leading-7 text-slate-400">The architecture treats evidence lineage, uncertainty, and change control as first-class engineering constraints.</p></div>
        <div className="mt-12 grid gap-4 lg:grid-cols-3">{capabilities.map(({ icon: Icon, eyebrow, title, body }) => <article key={title} className="group rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.035] to-transparent p-6 transition hover:border-cyan-300/20"><div className="flex items-center justify-between"><span className="grid h-10 w-10 place-items-center rounded-xl border border-cyan-300/15 bg-cyan-300/[0.07]"><Icon className="h-5 w-5 text-cyan-200" /></span><span className="text-[10px] uppercase tracking-[0.2em] text-slate-600">{eyebrow}</span></div><h3 className="mt-8 text-xl font-semibold tracking-tight text-white">{title}</h3><p className="mt-3 text-sm leading-6 text-slate-400">{body}</p></article>)}</div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-24 md:px-8 lg:pb-32"><div className="grid overflow-hidden rounded-3xl border border-white/[0.08] bg-[#090e15] lg:grid-cols-[0.85fr_1.15fr]"><div className="p-7 md:p-10"><div className="flex items-center gap-2 text-cyan-200"><GitPullRequestArrow className="h-4 w-4" /><span className="text-xs uppercase tracking-[0.2em]">System design</span></div><h2 className="mt-5 text-3xl font-semibold tracking-[-0.035em] text-white">From signal to safe recovery.</h2><p className="mt-4 text-sm leading-7 text-slate-400">A durable workflow connects telemetry, hybrid retrieval, adversarial verification, and a human-gated executor. Each transition persists enough state to survive restarts.</p><Link href="/topology" className="mt-7 inline-flex items-center gap-2 text-sm font-medium text-cyan-200">Explore service topology <ArrowRight className="h-4 w-4" /></Link></div><div className="border-t border-white/[0.08] bg-[#070b10] p-5 lg:border-l lg:border-t-0 md:p-8"><div className="grid gap-3 sm:grid-cols-3">{['Telemetry\nPrometheus · Loki · Tempo', 'Agent graph\nTriage · Investigate · Skeptic', 'Control plane\nApprove · Execute · Verify'].map((item, index) => { const [title, sub] = item.split('\n'); return <div key={title} className="relative rounded-xl border border-white/[0.08] bg-slate-950/70 p-4">{index < 2 && <ArrowRight className="absolute -right-2.5 top-1/2 z-10 hidden h-5 w-5 -translate-y-1/2 rounded-full bg-[#070b10] p-1 text-cyan-300 sm:block" />}<p className="text-xs font-medium text-white">{title}</p><p className="mt-2 text-[10px] leading-4 text-slate-600">{sub}</p></div>; })}</div><div className="mt-3 rounded-xl border border-white/[0.08] bg-slate-950/70 p-4"><div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-300" /><p className="text-xs font-medium text-white">Durable evidence and audit store</p></div><p className="mt-2 text-[10px] text-slate-600">PostgreSQL 16 · pgvector HNSW · Redis checkpoints · immutable action ledger</p></div></div></div></section>

      <section className="border-t border-white/[0.07] bg-[radial-gradient(circle_at_50%_100%,rgba(34,211,238,0.08),transparent_40%)]"><div className="mx-auto max-w-7xl px-5 py-20 text-center md:px-8"><Sparkles className="mx-auto h-6 w-6 text-cyan-200" /><h2 className="mx-auto mt-5 max-w-3xl text-4xl font-semibold tracking-[-0.04em] text-white md:text-5xl">Don’t read a feature list.<br />Walk the incident.</h2><p className="mx-auto mt-5 max-w-2xl text-sm leading-7 text-slate-400">Open the evidence timeline, inspect a ranked runbook, challenge the RCA, and review the bounded remediation plan.</p><Link href="/dashboard" className="group mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-950">Launch the console <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" /></Link><div className="mx-auto mt-12 flex max-w-4xl flex-wrap justify-center gap-x-6 gap-y-3">{stack.map((item) => <span key={item} className="font-mono text-[10px] uppercase tracking-wider text-slate-600">{item}</span>)}</div></div></section>

      <footer className="border-t border-white/[0.07] px-5 py-7"><div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 text-xs text-slate-600 sm:flex-row"><p>Built by Gautam Govind · Evidence over theatre.</p><div className="flex gap-5"><a href="https://github.com/Gautam2117/IncidentGraph" target="_blank" rel="noreferrer" className="hover:text-slate-300">GitHub</a><Link href="/evaluations" className="hover:text-slate-300">Evaluation proof</Link><Link href="/login" className="hover:text-slate-300">Operator sign-in</Link></div></div></footer>
    </main>
  );
}
