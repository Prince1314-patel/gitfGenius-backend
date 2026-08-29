import { NavLink, useLocation } from 'react-router-dom';
import { Home, Calendar, User, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Logo } from './Logo';
import { Button } from './ui/button';

const navItems = [
  { to: '/dashboard', icon: Home, label: 'Dashboard' },
  { to: '/calendar', icon: Calendar, label: 'Calendar' },
  { to: '/settings', icon: User, label: 'Settings' },
];

interface SidebarNavProps {
  onLogout: () => void;
}

export function SidebarNav({ onLogout }: SidebarNavProps) {
  const location = useLocation();

  return (
    <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-64 flex-col border-r border-border bg-card">
      <div className="p-6">
        <Logo />
      </div>

      <nav className="flex-1 px-4 py-2">
        <ul className="space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => {
            const isActive = location.pathname.startsWith(to);
            return (
              <li key={to}>
                <NavLink
                  to={to}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {label}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-border">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-muted-foreground"
          onClick={onLogout}
        >
          <LogOut className="h-5 w-5" />
          Sign Out
        </Button>
      </div>
    </aside>
  );
}
