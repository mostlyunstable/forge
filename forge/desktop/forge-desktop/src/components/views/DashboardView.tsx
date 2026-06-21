import { useProjects, useDecisions, useBugs, useIndexStatus } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { StatCard } from './dashboard/StatCard';
import { ActivityFeed } from './dashboard/ActivityFeed';
import { RiskFeed } from './dashboard/RiskFeed';
import { ModuleHealth } from './dashboard/ModuleHealth';

export function DashboardView() {
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const projectsQuery = useProjects();
  const decisionsQuery = useDecisions(currentProjectId);
  const bugsQuery = useBugs(currentProjectId);
  const indexQuery = useIndexStatus(currentProjectId);

  const totalProjects = projectsQuery.data?.total ?? 0;
  const totalDecisions = decisionsQuery.data?.total ?? 0;
  const openBugs = bugsQuery.data?.bugs?.filter((b) => !b.resolved).length ?? 0;
  const filesIndexed = indexQuery.data?.total_files_indexed ?? 0;

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-8 pt-8 pb-6">
        {/* Page header */}
        <div className="mb-8 flex items-end justify-between">
          <div>
            <h1 className="text-display-md">Dashboard</h1>
            <p className="mt-1 text-[13px] text-[var(--color-text-muted)]">
              Project overview and activity feed
            </p>
          </div>
          <select className="input w-auto text-[12px]">
            <option>Last 7 days</option>
            <option>Last 30 days</option>
            <option>All time</option>
          </select>
        </div>

        {/* Stats row */}
        <div className="mb-8 grid grid-cols-4 gap-4">
          <StatCard label="Projects" value={String(totalProjects)} icon="folder" />
          <StatCard label="Files Indexed" value={String(filesIndexed)} icon="code" />
          <StatCard label="Decisions" value={String(totalDecisions)} icon="git-branch" />
          <StatCard label="Open Bugs" value={String(openBugs)} icon="bug" />
        </div>

        {/* Content grid */}
        <div className="grid grid-cols-5 gap-6">
          <div className="col-span-3">
            <ActivityFeed />
          </div>
          <div className="col-span-2">
            <RiskFeed />
          </div>
        </div>

        {/* Module Health */}
        <div className="mt-6">
          <ModuleHealth />
        </div>
      </div>
    </div>
  );
}
