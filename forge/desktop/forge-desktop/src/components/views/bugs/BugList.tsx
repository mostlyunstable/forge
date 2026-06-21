import { cn } from '@/lib/utils';
import type { BugSummary } from '@/lib/api-types';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

interface BugListProps {
  bugs: BugSummary[];
  onSelect: (id: string) => void;
  selectedBug: string | null;
}

const severityConfig = {
  low: { color: 'text-[var(--color-risk-low)]', bg: 'bg-[var(--color-success-muted)]', label: 'Low' },
  medium: { color: 'text-[var(--color-risk-medium)]', bg: 'bg-[var(--color-warning-muted)]', label: 'Medium' },
  high: { color: 'text-[var(--color-risk-high)]', bg: 'bg-[var(--color-danger-muted)]', label: 'High' },
};

export function BugList({ bugs, onSelect, selectedBug }: BugListProps) {
  return (
    <div className="p-6">
      <div className="space-y-2">
        {bugs.length === 0 ? (
          <div className="rounded-lg border border-dashed border-[var(--color-border)] p-8 text-center text-[12px] text-[var(--color-text-faint)]">
            No bugs recorded
          </div>
        ) : (
          bugs.map((bug) => {
            const config = severityConfig[bug.severity as keyof typeof severityConfig] ?? severityConfig.medium;
            return (
              <button
                key={bug.id}
                onClick={() => onSelect(bug.id)}
                className={cn(
                  'card card-interactive w-full p-4 text-left',
                  selectedBug === bug.id && 'card-selected'
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-[13px] font-medium text-[var(--color-text-primary)] leading-snug">
                      {bug.title}
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <span className={cn('badge', config.bg, config.color)}>
                        {config.label}
                      </span>
                      {bug.resolved ? (
                        <span className="badge badge-success">
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          Resolved
                        </span>
                      ) : (
                        <span className="badge badge-warning">
                          <AlertTriangle className="mr-1 h-3 w-3" />
                          Open
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
