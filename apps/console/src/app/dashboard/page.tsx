import type { Metadata } from 'next';
import OperationalOverview from '@/components/OperationalOverview';

export const metadata: Metadata = { title: 'Engineering Console' };

export default function DashboardPage() {
  return <OperationalOverview />;
}
