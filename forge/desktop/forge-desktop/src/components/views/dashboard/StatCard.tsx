import { cn } from '@/lib/utils';
import { Folder, Code2, GitBranch, Bug } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string;
  trend?: number;
  icon?: 'folder' | 'code' | 'git-branch' | 'bug';
}

const iconMap = {
  folder: Folder,
  code: Code2,
  'git-branch': GitBranch,
  bug: Bug,
};

const iconColors = {
  folder: 'text-[var(--color-accent)]',
  code: 'text-[var(--color-info)]',
  'git-branch': 'text-[var(--color-success)]',
  bug: 'text-[var(--color-danger)]',
};

export function StatCard({ label, value, trend, icon }: StatCardProps) {
  const Icon = icon ? iconMap[icon] : null;

  return (
    <div className="card group p-4 transition-all duration-200">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-label">{label}</div>
          <div className="mt-2 text-display-sm">{value}</div>
        </div>
        {Icon && icon && (
          <div className="rounded-md bg-[var(--color-surface-elevated)] p-2 transition-colors duration-150 group-hover:bg-[var(--color-surface-overlay)]">
            <Icon className={cn('h-4 w-4', iconColors[icon])} />
          </div>
        )}
      </div>
      {trend !== undefined && trend !== 0 && (
        <div className={cn(
          'mt-3 flex items-center gap-1 text-[11px] font-medium',
          trend > 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'
        )}>
          <span>{trend > 0 ? '↑' : '↓'}</span>
          <span>{Math.abs(trend)}% from last week</span>
        </div>
      )}
    </div>
  );
}
