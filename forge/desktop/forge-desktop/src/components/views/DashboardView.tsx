import { useProjects, useDecisions, useBugs, useIndexStatus } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { SkeletonRow } from '@/components/ui/SkeletonRow';
import { ErrorState } from '@/components/ui/ErrorState';

export function DashboardView() {
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const projectsQuery = useProjects();
  const decisionsQuery = useDecisions(currentProjectId);
  const bugsQuery = useBugs(currentProjectId);
  const indexQuery = useIndexStatus(currentProjectId);

  const totalDecisions = decisionsQuery.data?.total ?? 0;
  const openBugs = bugsQuery.data?.bugs?.filter((b) => !b.resolved).length ?? 0;
  const filesIndexed = indexQuery.data?.total_files_indexed ?? 0;

  const isLoading = projectsQuery.isLoading || decisionsQuery.isLoading;

  if (projectsQuery.error) {
    return (
      <ErrorState
        code="API_ERROR"
        message="Failed to connect to Forge server. Check your connection settings."
        retry={() => projectsQuery.refetch()}
      />
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-6 pt-6 pb-4">
        {/* View header */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-display-sm">Dashboard</h1>
        </div>

        <div className="memory-pulse memory-pulse--active mb-6" />

        {/* Stats row — 3 columns */}
        {isLoading ? (
          <SkeletonRow lines={1} />
        ) : (
          <div className="mb-6 grid grid-cols-3 gap-4">
            <StatCard label="Total Memories" value={totalDecisions + openBugs} />
            <StatCard label="Open Bugs" value={openBugs} />
            <StatCard label="Decisions Made" value={totalDecisions} />
          </div>
        )}

        {/* Two-column split */}
        <div className="grid grid-cols-5 gap-6">
          {/* Recent Activity — left */}
          <div className="col-span-3">
            <h2 className="text-label mb-3">Recent Activity</h2>
            {isLoading ? (
              <SkeletonRow lines={5} />
            ) : (
              <div className="space-y-[1px]">
                {(decisionsQuery.data?.decisions ?? []).slice(0, 10).map((d) => (
                  <div
                    key={d.id}
                    className="flex items-center gap-3 border border-[var(--color-border-subtle)] rounded-[4px] px-3 py-2"
                  >
                    <span className="font-mono text-[12px] text-[var(--color-text-muted)] shrink-0 w-[140px]">
                      {new Date(d.created_at).toLocaleDateString()}
                    </span>
                    <span className="text-[13px] text-[var(--color-text-secondary)] truncate">
                      {d.title}
                    </span>
                  </div>
                ))}
                {(decisionsQuery.data?.decisions ?? []).length === 0 && (
                  <div className="text-[12px] text-[var(--color-text-muted)] py-4">
                    No activity yet. Record your first decision.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Risk Score — right */}
          <div className="col-span-2">
            <h2 className="text-label mb-3">Risk Score</h2>
            {isLoading ? (
              <SkeletonRow lines={3} />
            ) : (
              <div className="border border-[var(--color-border-subtle)] rounded-[4px] p-4">
                <div className="text-[32px] font-semibold text-[var(--color-text-primary)] font-[family-name:var(--font-display)]">
                  {filesIndexed}
                </div>
                <div className="text-[10px] uppercase tracking-[0.08em] text-[var(--color-text-muted)] mt-1">
                  Files Indexed
                </div>
                <div className="mt-4 h-[2px] w-full rounded-full bg-[var(--color-bg-elevated)]">
                  <div
                    className="h-[2px] rounded-full bg-[var(--color-accent-blue)]"
                    style={{ width: `${Math.min((filesIndexed / 100) * 100, 100)}%` }}
                  />
                </div>
                <div className="mt-2 text-[12px] text-[var(--color-text-muted)]">
                  {indexQuery.data?.running_job ? 'Indexing...' : 'Idle'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-[var(--color-border-subtle)] rounded-[4px] p-4">
      <div className="text-[32px] font-semibold text-[var(--color-text-primary)] font-[family-name:var(--font-display)]">
        {value}
      </div>
      <div className="text-[10px] uppercase tracking-[0.08em] text-[var(--color-text-muted)] mt-1">
        {label}
      </div>
    </div>
  );
}