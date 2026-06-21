import { cn } from '@/lib/utils';

interface Commit {
  hash: string;
  message: string;
  author: string;
  date: string;
  filesChanged: number;
}

const commits: Commit[] = [
  { hash: 'abc1234', message: 'feat: add chat endpoint', author: '@dev', date: '2h ago', filesChanged: 3 },
  { hash: 'def5678', message: 'fix: null pointer in auth', author: '@dev', date: '1d ago', filesChanged: 2 },
  { hash: 'ghi9012', message: 'refactor: extract context retriever', author: '@dev', date: '3d ago', filesChanged: 5 },
  { hash: 'jkl3456', message: 'feat: add indexing pipeline', author: '@dev', date: '5d ago', filesChanged: 12 },
];

interface CommitTimelineProps {
  onSelect: (hash: string) => void;
  selectedCommit: string | null;
}

export function CommitTimeline({ onSelect, selectedCommit }: CommitTimelineProps) {
  return (
    <div className="p-6">
      <div className="space-y-0">
        {commits.map((commit, i) => {
          const isSelected = selectedCommit === commit.hash;
          return (
            <div key={commit.hash} className="flex gap-4">
              {/* Timeline */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'h-3 w-3 rounded-full border-2 transition-all duration-150',
                    isSelected
                      ? 'border-[var(--color-accent)] bg-[var(--color-accent)] scale-110'
                      : 'border-[var(--color-border-strong)] bg-[var(--color-surface-raised)]'
                  )}
                />
                {i < commits.length - 1 && (
                  <div className="w-px flex-1 bg-[var(--color-border)]" />
                )}
              </div>

              {/* Content */}
              <button
                onClick={() => onSelect(commit.hash)}
                className={cn(
                  'mb-4 flex-1 rounded-lg border p-4 text-left transition-all duration-150',
                  isSelected
                    ? 'border-[var(--color-accent)] bg-[var(--color-accent-subtle)]'
                    : 'border-[var(--color-border)] bg-[var(--color-surface-raised)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-surface-elevated)]'
                )}
              >
                <div className="font-mono text-[12px] font-medium text-[var(--color-accent)]">
                  {commit.hash}
                </div>
                <div className="mt-1 text-[13px] font-medium text-[var(--color-text-primary)]">
                  {commit.message}
                </div>
                <div className="mt-2 flex items-center gap-3 text-[11px] text-[var(--color-text-faint)]">
                  <span>{commit.author}</span>
                  <span>·</span>
                  <span>{commit.date}</span>
                  <span>·</span>
                  <span>{commit.filesChanged} files</span>
                </div>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
