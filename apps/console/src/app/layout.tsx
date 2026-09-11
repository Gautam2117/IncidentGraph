import type { Metadata } from 'next';
import AppFrame from '@/components/AppFrame';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://incidentgraph.vercel.app'),
  title: {
    default: 'IncidentGraph — Autonomous AI Incident Control Plane',
    template: '%s | IncidentGraph',
  },
  description: 'Evidence-driven incident investigation, AI reliability evaluation, and human-gated remediation built with LangGraph, pgvector, and OpenTelemetry.',
  keywords: ['SRE', 'LangGraph', 'AI agents', 'incident response', 'OpenTelemetry', 'pgvector'],
  authors: [{ name: 'Gautam Govind', url: 'https://github.com/Gautam2117' }],
  openGraph: {
    title: 'IncidentGraph — Autonomous AI Incident Control Plane',
    description: 'Investigate with evidence. Remediate with control.',
    type: 'website',
  },
  twitter: { card: 'summary_large_image' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" data-scroll-behavior="smooth">
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col">
        <AppFrame>{children}</AppFrame>
      </body>
    </html>
  );
}
