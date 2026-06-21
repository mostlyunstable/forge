import { useCommandPalette } from '@/stores/command-palette';
import { Search, Command } from 'lucide-react';

export function TitleBar() {
  const commandPalette = useCommandPalette();

  return (
    <header
      data-tauri-drag-region
      className="flex h-[var(--titlebar-height)] items-center border-b border-[var(--color-border-subtle)] bg-[var(--color-surface)]"
    >
      {/* Spacer for macOS traffic lights */}
      <div className="w-[78px] shrink-0" />

      {/* Search trigger (centered) */}
      <div className="flex flex-1 items-center justify-center">
        <button
          onClick={commandPalette.open}
          className="flex items-center gap-2 rounded-md border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 text-[12px] text-[var(--color-text-faint)] transition-all duration-150 hover:border-[var(--color-border-strong)] hover:text-[var(--color-text-muted)]"
        >
          <Search className="h-3.5 w-3.5" />
          <span>Search commands...</span>
          <kbd className="ml-1 flex items-center gap-0.5 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text-faint)]">
            <Command className="h-2.5 w-2.5" />K
          </kbd>
        </button>
      </div>

      {/* Right spacer */}
      <div className="w-[78px] shrink-0" />
    </header>
  );
}
