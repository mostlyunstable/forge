import { GitCommit, GitPullRequest, FileText, Bug, ArrowRight } from 'lucide-react';

interface Activity {
  id: string;
  type: 'commit' | 'decision' | 'report' | 'bug';
  message: string;
  time: string;
}

const activities: Activity[] = [
  { id: '1', type: 'commit', message: 'Index completed: 266 files', time: '2h ago' },
  { id: '2', type: 'bug', message: '3 bugs extracted from commit history', time: '5h ago' },
  { id: '3', type: 'decision', message: 'Decision recorded: "Use FastAPI"', time: '1d ago' },
  { id: '4', type: 'report', message: 'PR #142 analyzed (risk: high)', time: '2d ago' },
  { id: '5', type: 'commit', message: 'Incremental index: 12 new files', time: '3d ago' },
];

const icons = {
  commit: GitCommit,
  decision: FileText,
  report: GitPullRequest,
  bug: Bug,
};

const iconBg = {
  commit: 'bg-[var(--color-info-muted)]',
  decision: 'bg-[var(--color-accent-muted)]',
  report: 'bg-[var(--color-warning-muted)]',
  bug: 'bg-[var(--color-danger-muted)]',
};

const iconColors = {
  commit: 'text-[var(--color-info)]',
  decision: 'text-[var(--color-accent)]',
  report: 'text-[var(--color-warning)]',
  bug: 'text-[var(--color-danger)]',
};

export function ActivityFeed() {
  return (
    <div className="card h-full">
      <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-5 py-3.5">
        <h3 className="text-[13px] font-semibold text-[var(--color-text-primary)]">Recent Activity</h3>
        <button className="flex items-center gap-1 text-[11px] font-medium text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] transition-colors">
          View all <ArrowRight className="h-3 w-3" />
        </button>
      </div>
      <div className="divide-y divide-[var(--color-border-subtle)]">
        {activities.map((activity) => {
          const Icon = icons[activity.type];
          return (
            <div key={activity.id} className="flex items-start gap-3 px-5 py-3.5 transition-colors hover:bg-[var(--color-surface-elevated)]">
              <div className={`mt-0.5 rounded-md p-1.5 ${iconBg[activity.type]}`}>
                <Icon className={`h-3.5 w-3.5 ${iconColors[activity.type]}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[13px] text-[var(--color-text-secondary)]">{activity.message}</div>
                <div className="mt-0.5 text-[11px] text-[var(--color-text-faint)]">{activity.time}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
