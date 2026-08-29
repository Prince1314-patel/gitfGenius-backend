import { ReactNode } from 'react';
import { BottomNav } from './BottomNav';
import { SidebarNav } from './SidebarNav';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <SidebarNav />
      
      <main className="pb-20 md:pb-0 md:pl-64">
        {children}
      </main>

      <BottomNav />
    </div>
  );
}
