import { getInitials } from '@/lib/dateUtils';
import { cn } from '@/lib/utils';

interface AvatarInitialsProps {
  name: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function AvatarInitials({ name, size = 'md', className }: AvatarInitialsProps) {
  const initials = getInitials(name);
  
  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-12 w-12 text-sm',
    lg: 'h-16 w-16 text-lg',
  };

  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-teal-100 font-semibold text-secondary",
        sizeClasses[size],
        className
      )}
    >
      {initials}
    </div>
  );
}
