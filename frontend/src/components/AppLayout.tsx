import { ReactNode } from 'react';
import { BottomNav } from './BottomNav';
import { SidebarNav } from './SidebarNav';

interface AppLayoutProps {
  children: ReactNode;
  onLogout: () => void;
}

export function AppLayout({ children, onLogout }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <SidebarNav onLogout={onLogout} />
      
      <main className="pb-20 md:pb-0 md:pl-64">
        {children}
      </main>

      <BottomNav />
    </div>
  );
}
