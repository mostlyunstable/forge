import { X, CheckCircle } from 'lucide-react';
import { useAnalysisReport } from '@/hooks/useApi';

interface ReportDetailProps {
  id: string;
  onClose: () => void;
}

export function ReportDetail({ id, onClose }: ReportDetailProps) {
  const { data: report, isLoading } = useAnalysisReport(id);

  return (
    <div className="p-5">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-display-sm">Report</h3>
        <button
          onClick={onClose}
          className="rounded-[4px] p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)] transition-colors"
        >
          <X className="h-[14px] w-[14px]" />
        </button>
      </div>

      {isLoading ? (
        <div className="flex h-32 items-center justify-center text-[var(--color-text-muted)]">
          <span className="text-[12px]">Loading...</span>
        </div>
      ) : !report ? (
        <div className="flex h-32 items-center justify-center text-[var(--color-text-muted)]">
          Not found
        </div>
      ) : (
        <div className="space-y-5">
          {/* Badges */}
          <div className="flex items-center gap-2">
            <span className={`badge ${
              report.risk_level === 'high' ? 'badge-red' :
              report.risk_level === 'medium' ? 'badge-amber' :
              'badge-green'
            }`}>
              {report.risk_level} Risk
            </span>
            <span className="badge-muted">
              {report.files_changed} files
            </span>
          </div>

          {/* Title */}
          <h4 className="text-[16px] font-semibold text-[var(--color-text-primary)] leading-snug">
            {report.title || `PR #${report.pr_number}`}
          </h4>

          {/* Summary */}
          {report.summary && (
            <div className="card p-4">
              <div className="text-label mb-2">Summary</div>
              <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
                {report.summary}
              </p>
            </div>
          )}

          {/* Risk Assessment */}
          <div className="card p-4">
            <div className="text-label mb-3">Risk Assessment</div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-[4px] bg-[var(--color-bg-elevated)] p-3 text-center">
                <div className="font-mono text-[18px] font-semibold text-[var(--color-text-primary)]">
                  {report.risk_score}/10
                </div>
                <div className="text-[11px] text-[var(--color-text-muted)]">Risk Score</div>
              </div>
              <div className="rounded-[4px] bg-[var(--color-bg-elevated)] p-3 text-center">
                <div className="font-mono text-[18px] font-semibold text-[var(--color-text-primary)]">
                  {report.blast_radius}
                </div>
                <div className="text-[11px] text-[var(--color-text-muted)]">Blast Radius</div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {report.recommendations.length > 0 && (
            <div className="card p-4">
              <div className="text-label mb-3">Recommendations</div>
              <div className="space-y-2.5">
                {report.recommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-[12px]">
                    <CheckCircle className="mt-0.5 h-[14px] w-[14px] shrink-0 text-[var(--color-accent-green)]" />
                    <span className="text-[var(--color-text-secondary)]">{rec.description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}