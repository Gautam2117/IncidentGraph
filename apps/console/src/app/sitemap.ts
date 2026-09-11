import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://incidentgraph.vercel.app';
  return ['/', '/dashboard', '/incidents', '/topology', '/scenarios', '/evaluations', '/knowledge'].map((path) => ({ url: `${base}${path}`, lastModified: new Date('2026-09-11'), changeFrequency: 'monthly' as const, priority: path === '/' ? 1 : 0.7 }));
}
