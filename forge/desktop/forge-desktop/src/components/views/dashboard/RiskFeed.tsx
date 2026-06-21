import { cn } from '@/lib/utils';
import { ArrowRight } from 'lucide-react';

interface RiskItem {
  id: string;
  module: string;
  level: 'low' | 'medium' | 'high';
  score: number;
}

const risks: RiskItem[] = [
  { id: '1', module: 'auth module', level: 'high', score: 8 },
  { id: '2', module: 'api routes', level: 'medium', score: 5 },
  { id: '3', module: 'tests', level: 'low', score: 2 },
];

const riskConfig = {
  low: { color: 'text-[var(--color-risk-low)]', bg: 'bg-[var(--color-risk-low)]', label: 'Low' },
  medium: { color: 'text-[var(--color-risk-medium)]', bg: 'bg-[var(--color-risk-medium)]', label: 'Medium' },
  high: { color: 'text-[var(--color-risk-high)]', bg: 'bg-[var(--color-risk-high)]', label: 'High' },
};

export function RiskFeed() {
  return (
    <div className="card h-full">
      <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-5 py-3.5">
        <h3 className="text-[13px] font-semibold text-[var(--color-text-primary)]">Risk Feed</h3>
        <button className="flex items-center gap-1 text-[11px] font-medium text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] transition-colors">
          View all <ArrowRight className="h-3 w-3" />
        </button>
      </div>
      <div className="divide-y divide-[var(--color-border-subtle)]">
        {risks.map((risk) => {
          const config = riskConfig[risk.level];
          return (
            <div key={risk.id} className="flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-[var(--color-surface-elevated)]">
              <div className={cn('h-2 w-2 rounded-full', config.bg)} />
              <div className="flex-1">
                <div className="text-[13px] text-[var(--color-text-secondary)]">{risk.module}</div>
              </div>
              <div className={cn('text-[11px] font-medium', config.color)}>
                {risk.score}/10
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
