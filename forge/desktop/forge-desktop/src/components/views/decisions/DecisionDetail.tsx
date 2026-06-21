import { X, GitBranch } from 'lucide-react';
import { useDecision } from '@/hooks/useApi';

interface DecisionDetailProps {
  id: string;
  onClose: () => void;
}

export function DecisionDetail({ id, onClose }: DecisionDetailProps) {
  const { data: decision, isLoading } = useDecision(id);

  return (
    <div className="p-5">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-display-sm">Decision</h3>
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
      ) : !decision ? (
        <div className="flex h-32 items-center justify-center text-[var(--color-text-faint)]">
          Not found
        </div>
      ) : (
        <div className="space-y-5">
          {/* Status badge */}
          <div className="flex items-center gap-2">
            <span className={`badge ${
              decision.status === 'accepted' ? 'badge-success' :
              decision.status === 'proposed' ? 'badge-accent' :
              'badge-muted'
            }`}>
              {decision.status}
            </span>
          </div>

          {/* Title */}
          <h4 className="text-[16px] font-semibold text-[var(--color-text-primary)] leading-snug">
            {decision.title}
          </h4>

          {/* Date */}
          <div className="text-[11px] text-[var(--color-text-faint)]">
            Created {new Date(decision.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </div>

          {/* Decision */}
          <div className="card p-4">
            <div className="text-label mb-2">Decision</div>
            <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
              {decision.decision}
            </p>
          </div>

          {/* Reason */}
          {decision.reason && (
            <div className="card p-4">
              <div className="text-label mb-2">Reason</div>
              <p className="text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
                {decision.reason}
              </p>
            </div>
          )}

          {/* Alternatives */}
          {decision.alternatives.length > 0 && (
            <div className="card p-4">
              <div className="text-label mb-2">Alternatives Considered</div>
              <div className="space-y-1.5">
                {decision.alternatives.map((alt, i) => (
                  <div key={i} className="flex items-center gap-2 rounded-md bg-[var(--color-surface-elevated)] px-3 py-2 text-[12px] text-[var(--color-text-secondary)]">
                    <GitBranch className="h-3 w-3 shrink-0 text-[var(--color-accent)]" />
                    <span>{alt}</span>
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
