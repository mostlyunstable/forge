import { useState } from 'react';
import { useDecisions } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { DecisionBoard } from './decisions/DecisionBoard';
import { DecisionDetail } from './decisions/DecisionDetail';

export function DecisionsView() {
  const [selectedDecision, setSelectedDecision] = useState<string | null>(null);
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const decisionsQuery = useDecisions(currentProjectId);

  const decisions = decisionsQuery.data?.decisions ?? [];

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-6 py-4">
          <div>
            <h2 className="text-display-sm">Decisions</h2>
            <p className="mt-0.5 text-[12px] text-[var(--color-text-faint)]">
              {decisions.length} decision{decisions.length !== 1 ? 's' : ''} recorded
            </p>
          </div>
          <button className="btn-primary">
            + New Decision
          </button>
        </div>
        {decisionsQuery.isLoading ? (
          <div className="flex h-64 items-center justify-center text-[var(--color-text-faint)]">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
              <span className="text-[12px]">Loading...</span>
            </div>
          </div>
        ) : (
          <DecisionBoard decisions={decisions} onSelect={setSelectedDecision} selectedDecision={selectedDecision} />
        )}
      </div>

      {selectedDecision && (
        <div className="w-[380px] shrink-0 border-l border-[var(--color-border-subtle)] bg-[var(--color-surface)] overflow-y-auto animate-slide-in-right">
          <DecisionDetail id={selectedDecision} onClose={() => setSelectedDecision(null)} />
        </div>
      )}
    </div>
  );
}
