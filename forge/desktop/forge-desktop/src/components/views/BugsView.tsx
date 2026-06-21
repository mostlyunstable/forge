import { useState } from 'react';
import { useBugs } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { BugList } from './bugs/BugList';
import { BugDetail } from './bugs/BugDetail';

export function BugsView() {
  const [selectedBug, setSelectedBug] = useState<string | null>(null);
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const bugsQuery = useBugs(currentProjectId);

  const bugList = bugsQuery.data?.bugs ?? [];

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-6 py-4">
          <div>
            <h2 className="text-display-sm">Bugs</h2>
            <p className="mt-0.5 text-[12px] text-[var(--color-text-faint)]">
              {bugList.length} bug{bugList.length !== 1 ? 's' : ''} tracked
            </p>
          </div>
          <button className="btn-primary">
            + New Bug
          </button>
        </div>
        {bugsQuery.isLoading ? (
          <div className="flex h-64 items-center justify-center text-[var(--color-text-faint)]">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
              <span className="text-[12px]">Loading...</span>
            </div>
          </div>
        ) : (
          <BugList bugs={bugList} onSelect={setSelectedBug} selectedBug={selectedBug} />
        )}
      </div>

      {selectedBug && (
        <div className="w-[380px] shrink-0 border-l border-[var(--color-border-subtle)] bg-[var(--color-surface)] overflow-y-auto animate-slide-in-right">
          <BugDetail id={selectedBug} onClose={() => setSelectedBug(null)} />
        </div>
      )}
    </div>
  );
}
