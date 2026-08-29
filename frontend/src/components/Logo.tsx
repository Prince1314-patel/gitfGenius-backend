import { Gift } from 'lucide-react';

export function Logo({ size = 'default' }: { size?: 'default' | 'large' }) {
  const iconSize = size === 'large' ? 'h-10 w-10' : 'h-8 w-8';
  const textSize = size === 'large' ? 'text-3xl' : 'text-2xl';

  return (
    <div className="flex items-center gap-2">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary">
        <Gift className={`${iconSize} text-primary-foreground`} />
      </div>
      <span className={`${textSize} font-bold text-primary`}>
        GiftGenius
      </span>
    </div>
  );
}
