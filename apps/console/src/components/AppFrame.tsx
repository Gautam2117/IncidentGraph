'use client';

import { usePathname } from 'next/navigation';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';

export default function AppFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname === '/' || pathname === '/login') {
    return <main className="min-h-screen">{children}</main>;
  }
  return (
    <>
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="max-w-[1600px] flex-1 overflow-x-hidden p-4 pb-24 md:p-6 md:pb-24 lg:pb-6">{children}</main>
      </div>
    </>
  );
}
