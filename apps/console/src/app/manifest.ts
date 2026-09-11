import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return { name: 'IncidentGraph', short_name: 'IncidentGraph', description: 'Autonomous AI incident control plane', start_url: '/', display: 'standalone', background_color: '#05080c', theme_color: '#22d3ee' };
}
