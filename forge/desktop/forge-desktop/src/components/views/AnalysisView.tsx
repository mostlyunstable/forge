import { useState } from 'react';
import { useAnalysisReports } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { ReportList } from './analysis/ReportList';
import { ReportDetail } from './analysis/ReportDetail';

export function AnalysisView() {
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const reportsQuery = useAnalysisReports(currentProjectId);

  const reports = reportsQuery.data?.reports ?? [];

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-hidden">
        <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-6 py-4">
          <div>
            <h2 className="text-display-sm">Analysis</h2>
            <p className="mt-0.5 text-[12px] text-[var(--color-text-faint)]">
              {reports.length} report{reports.length !== 1 ? 's' : ''}
            </p>
          </div>
          <button className="btn-primary">
            + Analyze PR
          </button>
        </div>
        {reportsQuery.isLoading ? (
          <div className="flex h-64 items-center justify-center text-[var(--color-text-faint)]">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
              <span className="text-[12px]">Loading...</span>
            </div>
          </div>
        ) : (
          <ReportList reports={reports} onSelect={setSelectedReport} selectedReport={selectedReport} />
        )}
      </div>

      {selectedReport && (
        <div className="w-[380px] shrink-0 border-l border-[var(--color-border-subtle)] bg-[var(--color-surface)] overflow-y-auto animate-slide-in-right">
          <ReportDetail id={selectedReport} onClose={() => setSelectedReport(null)} />
        </div>
      )}
    </div>
  );
}
