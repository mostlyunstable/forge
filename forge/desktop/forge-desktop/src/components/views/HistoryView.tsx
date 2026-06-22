import { useGitCommits } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { SkeletonRow } from '@/components/ui/SkeletonRow';
import { ErrorState } from '@/components/ui/ErrorState';

export function HistoryView() {
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const commitsQuery = useGitCommits(currentProjectId);

  const commits = commitsQuery.data?.commits ?? [];

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-6 pt-6 pb-4">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-display-sm">History</h1>
        </div>

        <div className="memory-pulse memory-pulse--active mb-6" />

        {commitsQuery.isLoading ? (
          <SkeletonRow lines={8} />
        ) : commitsQuery.error ? (
          <ErrorState
            code="API_ERROR"
            message="Failed to load commit history."
            retry={() => commitsQuery.refetch()}
          />
        ) : commits.length === 0 ? (
          <div className="text-[13px] text-[var(--color-text-muted)] py-8">
            No commits indexed yet. Run an index first.
          </div>
        ) : (
          <div className="space-y-[1px]">
            {commits.map((commit) => (
              <div
                key={commit.sha}
                className="flex items-center gap-4 border border-[var(--color-border-subtle)] rounded-[4px] px-3 py-2"
              >
                <span className="font-mono text-[12px] text-[var(--color-accent-cyan)] shrink-0 w-[64px]">
                  {commit.sha.slice(0, 7)}
                </span>
                <span className="flex-1 text-[13px] text-[var(--color-text-secondary)] truncate">
                  {commit.message}
                </span>
                <span className="text-[12px] text-[var(--color-text-muted)] shrink-0">
                  {commit.author}
                </span>
                <span className="font-mono text-[11px] text-[var(--color-text-muted)] shrink-0">
                  {new Date(commit.timestamp).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}