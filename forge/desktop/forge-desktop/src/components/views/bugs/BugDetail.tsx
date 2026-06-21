import { X, GitBranch } from 'lucide-react';
import { useBug } from '@/hooks/useApi';

interface BugDetailProps {
  id: string;
  onClose: () => void;
}

export function BugDetail({ id, onClose }: BugDetailProps) {
  const { data: bug, isLoading } = useBug(id);

  return (
    <div className="p-5">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-display-sm">Bug</h3>
        <button
          onClick={onClose}
          className="rounded-md p-1 text-[var(--color-text-faint)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-muted)] transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {isLoading ? (
        <div className="flex h-32 items-center justify-center text-[var(--color-text-faint)]">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
        </div>
      ) : !bug ? (
        <div className="flex h-32 items-center justify-center text-[var(--color-text-faint)]">
          Not found
        </div>
      ) : (
        <div className="space-y-5">
          {/* Badges */}
          <div className="flex items-center gap-2">
            <span className={`badge ${
              bug.severity === 'high' ? 'badge-danger' :
              bug.severity === 'medium' ? 'badge-warning' :
              'badge-success'
            }`}>
              {bug.severity}
            </span>
            <span className={`badge ${bug.resolved ? 'badge-success' : 'badge-warning'}`}>
              {bug.resolved ? 'Resolved' : 'Open'}
            </span>
          </div>

          {/* Title */}
          <h4 className="text-[16px] font-semibold text-[var(--color-text-primary)] leading-snug">
            {bug.title}
          </h4>

          {/* Date */}
          <div className="text-[11px] text-[var(--color-text-faint)]">
            Created {new Date(bug.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </div>

          {/* Problem */}
          <div className="card p-4">
            <div className="text-label mb-2">Problem</div>
            <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
              {bug.problem}
            </p>
          </div>

          {/* Root Cause */}
          {bug.root_cause && (
            <div className="card p-4">
              <div className="text-label mb-2">Root Cause</div>
              <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
                {bug.root_cause}
              </p>
            </div>
          )}

          {/* Solution */}
          {bug.solution && (
            <div className="card p-4">
              <div className="text-label mb-2">Solution</div>
              <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
                {bug.solution}
              </p>
            </div>
          )}

          {/* Affected Code */}
          {bug.affected_files.length > 0 && (
            <div className="card p-4">
              <div className="text-label mb-2">Affected Code</div>
              <div className="space-y-1.5">
                {bug.affected_files.map((file) => (
                  <div key={file} className="flex items-center gap-2 rounded-md bg-[var(--color-surface-elevated)] px-3 py-2 text-[12px] text-[var(--color-text-secondary)]">
                    <GitBranch className="h-3 w-3 shrink-0 text-[var(--color-accent)]" />
                    <span className="font-mono text-[11px]">{file}</span>
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
