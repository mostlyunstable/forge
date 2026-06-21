import { useState } from 'react';
import { useSearchCode, useFileEntries } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { FileTree } from './code/FileTree';
import { CodeViewer } from './code/CodeViewer';
import { CodeInsightPanel } from './code/CodeInsightPanel';
import { CodeFilters } from './code/CodeFilters';

export function CodeView() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const currentProjectId = useSettings((s) => s.currentProjectId);

  const searchQueryResult = useSearchCode(searchQuery, searchQuery && currentProjectId ? currentProjectId : null);
  const fileEntries = useFileEntries(currentProjectId, selectedFile);

  return (
    <div className="flex h-full">
      {/* Sidebar: file tree / search */}
      <div className="w-[240px] shrink-0 border-r border-[var(--color-border-subtle)] bg-[var(--color-surface)]">
        <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-3 py-2.5">
          <span className="text-[12px] font-semibold text-[var(--color-text-secondary)]">Files</span>
        </div>
        <CodeFilters onSearch={setSearchQuery} />
        {searchQuery && searchQueryResult.data ? (
          <div className="overflow-y-auto py-1">
            {searchQueryResult.data.results.length === 0 ? (
              <div className="px-3 py-6 text-center text-[12px] text-[var(--color-text-faint)]">No results</div>
            ) : (
              searchQueryResult.data.results.map((entry) => (
                <button
                  key={entry.id}
                  onClick={() => {
                    setSelectedFile(entry.file_path);
                    setSearchQuery('');
                  }}
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-secondary)] transition-colors"
                >
                  <span className="truncate font-mono text-[11px]">{entry.name}</span>
                  <span className="shrink-0 text-[10px] text-[var(--color-text-faint)]">{entry.entry_type}</span>
                </button>
              ))
            )}
          </div>
        ) : (
          <FileTree onSelect={setSelectedFile} selectedFile={selectedFile} />
        )}
      </div>

      {/* Main: code viewer */}
      <div className="flex-1 overflow-hidden bg-[var(--color-background)]">
        {selectedFile ? (
          <CodeViewer
            filePath={selectedFile}
            entries={fileEntries.data?.entries ?? []}
            isLoading={fileEntries.isLoading}
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-[var(--color-text-faint)]">
            <div className="rounded-xl bg-[var(--color-surface-raised)] p-4">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
              </svg>
            </div>
            <div className="text-[13px] font-medium">Select a file to view</div>
            <div className="text-[11px]">Choose from the file tree or search above</div>
          </div>
        )}
      </div>

      {/* Right: insight panel */}
      {selectedFile && (
        <div className="w-[320px] shrink-0 border-l border-[var(--color-border-subtle)] bg-[var(--color-surface)] overflow-y-auto animate-slide-in-right">
          <CodeInsightPanel filePath={selectedFile} entries={fileEntries.data?.entries ?? []} />
        </div>
      )}
    </div>
  );
}
