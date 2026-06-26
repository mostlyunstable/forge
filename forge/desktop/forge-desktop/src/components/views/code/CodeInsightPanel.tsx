import type { FileEntry } from '@/lib/api-types';
import { GitBranch } from 'lucide-react';

interface CodeInsightPanelProps {
  filePath: string;
  entries: FileEntry[];
}

export function CodeInsightPanel({ entries }: CodeInsightPanelProps) {
  const entryTypes = entries.reduce((acc, e) => {
    acc[e.entry_type] = (acc[e.entry_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="p-4 space-y-5">
      {/* File Summary */}
      <div className="card p-4">
        <div className="text-label mb-3">File Summary</div>
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-[4px] bg-[var(--color-bg-elevated)] p-3 text-center">
            <div className="font-mono text-[18px] font-semibold text-[var(--color-text-primary)]">
              {entries.length}
            </div>
            <div className="text-[11px] text-[var(--color-text-muted)]">Entries</div>
          </div>
          <div className="rounded-[4px] bg-[var(--color-bg-elevated)] p-3 text-center">
            <div className="font-mono text-[14px] font-semibold text-[var(--color-text-primary)]">
              {entries[0]?.language || '—'}
            </div>
            <div className="text-[11px] text-[var(--color-text-muted)]">Language</div>
          </div>
        </div>
      </div>

      {/* Entry Types */}
      {Object.keys(entryTypes).length > 0 && (
        <div className="card p-4">
          <div className="text-label mb-3">Entry Types</div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(entryTypes).map(([type, count]) => (
              <span key={type} className="badge-muted">
                {type}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Entries List */}
      {entries.length > 0 && (
        <div className="card p-4">
          <div className="text-label mb-3">Entries in File</div>
          <div className="space-y-2">
            {entries.map((entry, i) => (
              <div key={i} className="flex items-center gap-2.5 rounded-[4px] bg-[var(--color-bg-elevated)] px-3 py-2 transition-colors hover:bg-[var(--color-bg-overlay)]">
                <GitBranch className="h-[14px] w-[14px] shrink-0 text-[var(--color-accent-blue)]" />
                <span className="flex-1 truncate font-mono text-[11px] font-medium text-[var(--color-text-primary)]">
                  {entry.name}
                </span>
                <span className="text-[10px] text-[var(--color-text-muted)]">
                  L{entry.start_line}–{entry.end_line}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}