import { useState } from 'react';
import { CommitTimeline } from './history/CommitTimeline';
import { CommitDetail } from './history/CommitDetail';

export function HistoryView() {
  const [selectedCommit, setSelectedCommit] = useState<string | null>(null);

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-hidden">
        <div className="border-b border-[var(--color-border-subtle)] px-6 py-4">
          <h2 className="text-display-sm">History</h2>
          <p className="mt-0.5 text-[12px] text-[var(--color-text-faint)]">
            Commit timeline and changes
          </p>
        </div>
        <CommitTimeline onSelect={setSelectedCommit} selectedCommit={selectedCommit} />
      </div>

      {selectedCommit && (
        <div className="w-[380px] shrink-0 border-l border-[var(--color-border-subtle)] bg-[var(--color-surface)] overflow-y-auto animate-slide-in-right">
          <CommitDetail id={selectedCommit} onClose={() => setSelectedCommit(null)} />
        </div>
      )}
    </div>
  );
}
