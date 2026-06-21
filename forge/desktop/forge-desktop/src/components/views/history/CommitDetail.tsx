import { X, FileText, Plus, Minus } from 'lucide-react';

interface CommitDetailProps {
  id: string;
  onClose: () => void;
}

export function CommitDetail({ id, onClose }: CommitDetailProps) {
  return (
    <div className="p-5">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-display-sm">Commit</h3>
        <button
          onClick={onClose}
          className="rounded-md p-1 text-[var(--color-text-faint)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-muted)] transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Header */}
      <div className="mb-5">
        <div className="font-mono text-[13px] font-medium text-[var(--color-accent)]">{id}</div>
        <h4 className="mt-1 text-[15px] font-semibold text-[var(--color-text-primary)]">
          feat: add chat endpoint
        </h4>
        <div className="mt-2 flex items-center gap-3 text-[11px] text-[var(--color-text-faint)]">
          <span>@dev</span>
          <span>·</span>
          <span>2 hours ago</span>
        </div>
      </div>

      {/* Files Changed */}
      <div className="card p-4">
        <div className="text-label mb-3">Files Changed</div>
        <div className="space-y-1.5">
          {[
            { file: 'forge/presentation/routes/chat.py', added: 45, removed: 0 },
            { file: 'forge/application/chat.py', added: 32, removed: 5 },
            { file: 'forge/domain/chat.py', added: 12, removed: 0 },
          ].map((change) => (
            <div key={change.file} className="flex items-center gap-2 rounded-md bg-[var(--color-surface-elevated)] px-3 py-2 text-[12px]">
              <FileText className="h-3 w-3 shrink-0 text-[var(--color-accent)]" />
              <span className="flex-1 truncate font-mono text-[11px] text-[var(--color-text-secondary)]">
                {change.file}
              </span>
              <span className="flex items-center gap-1.5 text-[10px] tabular-nums">
                <span className="flex items-center gap-0.5 text-[var(--color-success)]">
                  <Plus className="h-2.5 w-2.5" />
                  {change.added}
                </span>
                {change.removed > 0 && (
                  <span className="flex items-center gap-0.5 text-[var(--color-danger)]">
                    <Minus className="h-2.5 w-2.5" />
                    {change.removed}
                  </span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
