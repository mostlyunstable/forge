import { Network } from 'lucide-react';

export function GraphView() {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-6 py-4">
        <div>
          <h2 className="text-display-sm">Knowledge Graph</h2>
          <p className="mt-0.5 text-[12px] text-[var(--color-text-faint)]">
            Visualize relationships between code, decisions, and bugs
          </p>
        </div>
        <div className="flex gap-2">
          <select className="input w-auto text-[12px]">
            <option>Force-directed</option>
            <option>Hierarchical</option>
            <option>Circular</option>
          </select>
        </div>
      </div>

      <div className="flex-1 relative bg-[var(--color-background)]">
        {/* Placeholder */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-surface-raised)]">
              <Network className="h-8 w-8 text-[var(--color-text-faint)]" />
            </div>
            <div className="text-[14px] font-medium text-[var(--color-text-muted)]">
              Knowledge graph visualization
            </div>
            <div className="mt-1 text-[12px] text-[var(--color-text-faint)]">
              Requires D3.js or similar graph library
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-3">
          <div className="text-label mb-2">Legend</div>
          <div className="space-y-1.5 text-[11px]">
            {[
              { color: 'bg-[var(--color-accent)]', label: 'Decision' },
              { color: 'bg-[var(--color-info)]', label: 'Code' },
              { color: 'bg-[var(--color-danger)]', label: 'Bug' },
              { color: 'bg-[var(--color-success)]', label: 'Commit' },
              { color: 'bg-[var(--color-warning)]', label: 'Developer' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${item.color}`} />
                <span className="text-[var(--color-text-muted)]">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
