import { cn } from '@/lib/utils';

interface BirthdayBadgeProps {
  text: string;
  isUrgent: boolean;
  className?: string;
}

export function BirthdayBadge({ text, isUrgent, className }: BirthdayBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
        isUrgent
          ? "bg-primary text-primary-foreground"
          : "text-secondary",
        className
      )}
    >
      {text}
    </span>
  );
}
