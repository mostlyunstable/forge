import { cn } from '@/lib/utils';
import type { AnalysisReportSummary } from '@/lib/api-types';

interface ReportListProps {
  reports: AnalysisReportSummary[];
  onSelect: (id: string) => void;
  selectedReport: string | null;
}

const riskConfig = {
  low: { color: 'text-[var(--color-risk-low)]', bg: 'bg-[var(--color-success-muted)]', label: 'Low' },
  medium: { color: 'text-[var(--color-risk-medium)]', bg: 'bg-[var(--color-warning-muted)]', label: 'Medium' },
  high: { color: 'text-[var(--color-risk-high)]', bg: 'bg-[var(--color-danger-muted)]', label: 'High' },
};

export function ReportList({ reports, onSelect, selectedReport }: ReportListProps) {
  return (
    <div className="p-6">
      <div className="space-y-2">
        {reports.length === 0 ? (
          <div className="rounded-lg border border-dashed border-[var(--color-border)] p-8 text-center text-[12px] text-[var(--color-text-faint)]">
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
                    <div className="mt-2 flex items-center gap-3 text-[11px] text-[var(--color-text-faint)]">
                      <span>{report.files_changed} files</span>
                      <span>·</span>
                      <span>Risk {report.risk_score}/10</span>
                      <span>·</span>
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <span className={cn('badge', config.bg, config.color)}>
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
