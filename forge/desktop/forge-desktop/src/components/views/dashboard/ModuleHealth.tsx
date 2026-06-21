import { cn } from '@/lib/utils';

interface Module {
  name: string;
  health: number;
  risk: 'low' | 'medium' | 'high';
}

const modules: Module[] = [
  { name: 'domain', health: 82, risk: 'low' },
  { name: 'application', health: 68, risk: 'medium' },
  { name: 'infrastructure', health: 95, risk: 'low' },
  { name: 'presentation', health: 45, risk: 'high' },
];

const riskConfig = {
  low: { color: 'text-[var(--color-risk-low)]', bar: 'bg-[var(--color-risk-low)]' },
  medium: { color: 'text-[var(--color-risk-medium)]', bar: 'bg-[var(--color-risk-medium)]' },
  high: { color: 'text-[var(--color-risk-high)]', bar: 'bg-[var(--color-risk-high)]' },
};

export function ModuleHealth() {
  return (
    <div className="card">
      <div className="border-b border-[var(--color-border-subtle)] px-5 py-3.5">
        <h3 className="text-[13px] font-semibold text-[var(--color-text-primary)]">Module Health</h3>
      </div>
      <div className="divide-y divide-[var(--color-border-subtle)]">
        {modules.map((mod) => {
          const config = riskConfig[mod.risk];
          return (
            <div key={mod.name} className="flex items-center gap-4 px-5 py-3.5">
              <div className="w-28 font-mono text-[12px] font-medium text-[var(--color-text-secondary)]">{mod.name}</div>
              <div className="flex-1">
                <div className="h-1.5 rounded-full bg-[var(--color-surface-elevated)]">
                  <div
                    className={cn('h-full rounded-full transition-all duration-500', config.bar)}
                    style={{ width: `${mod.health}%` }}
                  />
                </div>
              </div>
              <div className="w-10 text-right font-mono text-[11px] font-medium tabular-nums text-[var(--color-text-muted)]">
                {mod.health}%
              </div>
              <div className={cn('w-16 text-right text-[11px] font-medium capitalize', config.color)}>
                {mod.risk}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
