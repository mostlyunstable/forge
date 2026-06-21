import { useState } from 'react';
import { DecisionCard } from './DecisionCard';
import type { DecisionSummary } from '@/lib/api-types';

interface DecisionBoardProps {
  decisions: DecisionSummary[];
  onSelect: (id: string) => void;
  selectedDecision: string | null;
}

const columns = [
  { status: 'proposed' as const, label: 'Proposed', color: 'var(--color-info)' },
  { status: 'accepted' as const, label: 'Accepted', color: 'var(--color-success)' },
  { status: 'superseded' as const, label: 'Superseded', color: 'var(--color-text-faint)' },
];

export function DecisionBoard({ decisions, onSelect, selectedDecision }: DecisionBoardProps) {
  const [filter, setFilter] = useState<string>('all');
  const filtered = filter === 'all' ? decisions : decisions.filter((d) => d.status === filter);

  return (
    <div className="p-6">
      {/* Filter pills */}
      <div className="mb-6 flex gap-1.5">
        {['all', 'proposed', 'accepted', 'superseded'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-[12px] font-medium transition-all duration-150 ${
              filter === f
                ? 'bg-[var(--color-accent)] text-white'
                : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-secondary)]'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Kanban columns */}
      <div className="grid grid-cols-3 gap-4">
        {columns.map((col) => {
          const colDecisions = filtered.filter((d) => d.status === col.status);
          return (
            <div key={col.status}>
              <div className="mb-3 flex items-center gap-2 px-1">
                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: col.color }} />
                <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-faint)]">
                  {col.label}
                </span>
                <span className="text-[11px] text-[var(--color-text-faint)]">({colDecisions.length})</span>
              </div>
              <div className="space-y-2">
                {colDecisions.map((decision) => (
                  <DecisionCard
                    key={decision.id}
                    decision={decision}
                    isSelected={selectedDecision === decision.id}
                    onSelect={onSelect}
                  />
                ))}
                {colDecisions.length === 0 && (
                  <div className="rounded-lg border border-dashed border-[var(--color-border)] p-4 text-center text-[11px] text-[var(--color-text-faint)]">
                    No items
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
