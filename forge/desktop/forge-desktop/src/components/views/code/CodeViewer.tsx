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
    <div className="flex group/line h-[22px] hover:bg-[var(--color-bg-elevated)]">
      <span className="w-12 shrink-0 select-none pr-4 text-right font-mono text-[11px] text-[var(--color-text-muted)] group-hover/line:text-[var(--color-text-secondary)]">
        {number}
      </span>
      <span className="flex-1 font-mono text-[12px] text-[var(--color-text-primary)]">
        {content}
      </span>
    </div>
  );
}

export function CodeViewer({ filePath, entries, isLoading }: CodeViewerProps) {
  const [copied, setCopied] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-[var(--color-text-muted)]">
        <span className="text-[12px]">Loading...</span>
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
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--color-border-subtle)] bg-[var(--color-bg-surface)] px-4 py-2">
        <div className="flex items-center gap-2">
          <FileCode className="h-[14px] w-[14px] text-[var(--color-accent-blue)]" />
          <span className="font-mono text-[12px] text-[var(--color-text-secondary)]">{filePath}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-[4px] px-2 py-1 text-[11px] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)] transition-colors"
        >
          {copied ? (
            <>
              <Check className="h-[14px] w-[14px] text-[var(--color-accent-green)]" />
              <span className="text-[var(--color-accent-green)]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-[14px] w-[14px]" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      {entries.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center gap-2 text-[var(--color-text-muted)]">
          <FileCode className="h-[32px] w-[32px]" />
          <div className="text-[13px]">No entries indexed for this file</div>
        </div>
      ) : (
        <div>
          {entries.map((entry, i) => {
            const lines = (entry.content || '// Content not available').split('\n');
            return (
              <div key={i}>
                {/* Entry header */}
                <div className="flex items-center gap-2 border-b border-[var(--color-border-subtle)] bg-[var(--color-bg-base)] px-4 py-2">
                  <span className="badge-blue">{entry.entry_type}</span>
                  <span className="font-mono text-[12px] font-medium text-[var(--color-text-primary)]">
                    {entry.name}
                  </span>
                  <span className="text-[11px] text-[var(--color-text-muted)]">
                    L{entry.start_line}–{entry.end_line}
                  </span>
                </div>

                {/* Code block */}
                <div className="overflow-x-auto bg-[var(--color-bg-surface)] px-4 py-3">
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