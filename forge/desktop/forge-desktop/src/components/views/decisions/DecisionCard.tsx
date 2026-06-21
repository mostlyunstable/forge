import { cn } from '@/lib/utils';
import type { DecisionSummary } from '@/lib/api-types';
import { Calendar } from 'lucide-react';

interface DecisionCardProps {
  decision: DecisionSummary;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

export function DecisionCard({ decision, isSelected, onSelect }: DecisionCardProps) {
  const dateStr = decision.created_at
    ? new Date(decision.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : '';

  return (
    <button
      onClick={() => onSelect(decision.id)}
      className={cn(
        'card card-interactive w-full p-3.5 text-left',
        isSelected && 'card-selected'
      )}
    >
      <div className="text-[13px] font-medium text-[var(--color-text-primary)] leading-snug">
        {decision.title}
      </div>
      <div className="mt-2 flex items-center gap-2 text-[11px] text-[var(--color-text-faint)]">
        <Calendar className="h-3 w-3" />
        <span>{dateStr}</span>
      </div>
    </button>
  );
}
