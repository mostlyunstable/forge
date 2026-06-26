import { cn } from '@/lib/utils';
import type { AnalysisReportSummary } from '@/lib/api-types';

interface ReportListProps {
  reports: AnalysisReportSummary[];
  onSelect: (id: string) => void;
  selectedReport: string | null;
}

const riskConfig = {
  low: { color: 'text-[var(--color-accent-green)]', label: 'Low' },
  medium: { color: 'text-[var(--color-accent-amber)]', label: 'Medium' },
  high: { color: 'text-[var(--color-accent-red)]', label: 'High' },
};

export function ReportList({ reports, onSelect, selectedReport }: ReportListProps) {
  return (
    <div className="p-6">
      <div className="space-y-2">
        {reports.length === 0 ? (
          <div className="rounded-[4px] border border-dashed border-[var(--color-border-subtle)] p-8 text-center text-[12px] text-[var(--color-text-muted)]">
            No analysis reports yet
          </div>
        ) : (
          reports.map((report) => {
            const config = riskConfig[report.risk_level as keyof typeof riskConfig] ?? riskConfig.medium;
            return (
              <button
                key={report.id}
                onClick={() => onSelect(report.id)}
                className={cn(
                  'card card-interactive w-full p-4 text-left',
                  selectedReport === report.id && 'card-selected'
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-[13px] font-medium text-[var(--color-text-primary)] leading-snug">
                      {report.title || `PR #${report.pr_number}`}
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-[11px] text-[var(--color-text-muted)]">
                      <span>{report.files_changed} files</span>
                      <span>·</span>
                      <span>Risk {report.risk_score}/10</span>
                      <span>·</span>
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <span className={cn('badge-muted', config.color)}>
                    {config.label}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}