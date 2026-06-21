import type { FileEntry } from '@/lib/api-types';
import { FileCode, Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface CodeViewerProps {
  filePath: string;
  entries: FileEntry[];
  isLoading: boolean;
}

function CodeLine({ number, content }: { number: number; content: string }) {
  return (
    <div className="flex hover:bg-[var(--color-surface-elevated)]/50 group/line">
      <span className="w-12 shrink-0 select-none pr-4 text-right font-mono text-[11px] leading-[1.7] text-[var(--color-text-faint)] group-hover/line:text-[var(--color-text-muted)]">
        {number}
      </span>
      <span className="flex-1 font-mono text-[12px] leading-[1.7] text-[var(--color-text-secondary)]">
        <span className="text-[var(--color-text-primary)]">{content}</span>
      </span>
    </div>
  );
}

export function CodeViewer({ filePath, entries, isLoading }: CodeViewerProps) {
  const [copied, setCopied] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-[var(--color-text-faint)]">
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
          <span className="text-[12px]">Loading...</span>
        </div>
      </div>
    );
  }

  const handleCopy = () => {
    const allContent = entries.map((e) => e.content).join('\n\n');
    navigator.clipboard.writeText(allContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full overflow-auto">
      {/* File header bar */}
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--color-border-subtle)] bg-[var(--color-surface-raised)]/95 px-4 py-2 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <FileCode className="h-4 w-4 text-[var(--color-accent)]" />
          <span className="font-mono text-[12px] text-[var(--color-text-secondary)]">{filePath}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] text-[var(--color-text-faint)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-muted)] transition-colors"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-[var(--color-success)]" />
              <span className="text-[var(--color-success)]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      {entries.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center gap-2 text-[var(--color-text-faint)]">
          <FileCode className="h-8 w-8" />
          <div className="text-[13px]">No entries indexed for this file</div>
        </div>
      ) : (
        <div className="divide-y divide-[var(--color-border-subtle)]">
          {entries.map((entry, i) => {
            const lines = (entry.content || '// Content not available').split('\n');
            return (
              <div key={i} className="animate-fade-in">
                {/* Entry header */}
                <div className="flex items-center gap-2 border-b border-[var(--color-border-subtle)] bg-[var(--color-surface)] px-4 py-2">
                  <span className="badge-accent">{entry.entry_type}</span>
                  <span className="font-mono text-[12px] font-medium text-[var(--color-text-primary)]">
                    {entry.name}
                  </span>
                  <span className="text-[11px] text-[var(--color-text-faint)]">
                    L{entry.start_line}–{entry.end_line}
                  </span>
                </div>

                {/* Code block */}
                <div className="overflow-x-auto bg-[var(--color-background)] px-4 py-3">
                  <div className="min-w-max">
                    {lines.map((line, lineNum) => (
                      <CodeLine
                        key={lineNum}
                        number={entry.start_line + lineNum}
                        content={line}
                      />
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
