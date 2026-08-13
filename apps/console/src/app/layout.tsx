import type { Metadata } from 'next';
import AppFrame from '@/components/AppFrame';
import './globals.css';

export const metadata: Metadata = {
  title: 'IncidentGraph — Autonomous AI Incident Control Plane',
  description: 'Multi-role AI agent incident investigation, reliability evaluation & controlled remediation platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col">
        <AppFrame>{children}</AppFrame>
      </body>
    </html>
  );
}
