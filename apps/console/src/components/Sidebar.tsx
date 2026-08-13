'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const sections = [
  { label: 'Operate', items: [
    { label: 'Overview', href: '/' },
    { label: 'Incidents', href: '/incidents' },
    { label: 'Topology', href: '/topology' },
    { label: 'Chaos scenarios', href: '/scenarios' },
  ] },
  { label: 'Improve', items: [
    { label: 'Evaluations', href: '/evaluations' },
    { label: 'Knowledge', href: '/knowledge' },
    { label: 'Audit trail', href: '/audit' },
  ] },
  { label: 'Configure', items: [
    { label: 'Models', href: '/settings/models' },
    { label: 'Retrieval', href: '/settings/retrieval' },
    { label: 'Webhooks', href: '/settings/webhooks' },
  ] },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden lg:block w-60 border-r border-white/10 bg-[#080c12] p-4 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6 sticky top-20">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="px-3 mb-2 text-[10px] uppercase tracking-[0.2em] text-slate-600">{section.label}</p>
            <div className="space-y-1">
              {section.items.map((item) => {
                const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                return <Link key={item.href} href={item.href} className={`block rounded-lg px-3 py-2 text-sm transition ${active ? 'bg-cyan-400/10 text-cyan-200 border border-cyan-400/20' : 'text-slate-400 border border-transparent hover:bg-white/[0.03] hover:text-white'}`}>{item.label}</Link>;
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
