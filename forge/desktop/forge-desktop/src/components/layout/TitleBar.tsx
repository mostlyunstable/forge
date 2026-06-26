import { useSettings } from '@/stores/settings';
import { useProjects } from '@/hooks/useApi';
import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { checkServerConnection } from '@/lib/api';

export function TitleBar() {
  const { currentProjectId, setCurrentProject, connectionStatus, setConnectionStatus, apiUrl } = useSettings();
  const projectsQuery = useProjects();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Check connection on mount and when apiUrl changes
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      setConnectionStatus('checking');
      const connected = await checkServerConnection(apiUrl);
      if (!cancelled) {
        setConnectionStatus(connected ? 'connected' : 'disconnected');
      }
    };
    check();
    return () => { cancelled = true; };
  }, [apiUrl]);

  const projects = projectsQuery.data?.projects ?? [];
  const currentProject = projects.find((p) => p.id === currentProjectId);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <header
      data-tauri-drag-region
      className="flex h-[var(--titlebar-height)] items-center border-b border-[var(--color-border-subtle)] bg-[var(--color-bg-base)]"
    >
      {/* Spacer for macOS traffic lights */}
      <div className="w-[78px] shrink-0" />

      {/* Center: Project selector */}
      <div className="flex flex-1 items-center justify-center">
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-1 rounded-[4px] px-2 py-1 text-[13px] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] transition-colors duration-120"
          >
            <span>{currentProject?.name ?? 'No Project'}</span>
            <ChevronDown className="h-[12px] w-[12px] text-[var(--color-text-muted)]" />
          </button>

          {dropdownOpen && (
            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 min-w-[200px] rounded-[4px] border border-[var(--color-border-default)] bg-[var(--color-bg-overlay)] py-1 z-50">
              {projects.length === 0 ? (
                <div className="px-3 py-2 text-[12px] text-[var(--color-text-muted)]">
                  No projects found
                </div>
              ) : (
                projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => {
                      setCurrentProject(project.id);
                      setDropdownOpen(false);
                    }}
                    className={`flex w-full items-center px-3 py-[6px] text-[12px] transition-colors duration-120 ${
                      project.id === currentProjectId
                        ? 'bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)]'
                        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)]'
                    }`}
                  >
                    <span className="truncate">{project.name}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Right: Connection status + settings */}
      <div className="flex items-center gap-3 pr-4">
        <div className="flex items-center gap-2 text-[11px] text-[var(--color-text-muted)]">
          <span className={`h-[6px] w-[6px] rounded-full ${
            connectionStatus === 'connected' ? 'bg-[var(--color-accent-green)]' :
            connectionStatus === 'disconnected' ? 'bg-[var(--color-accent-red)]' :
            'bg-[var(--color-accent-amber)]'
          }`} />
          <span>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'disconnected' ? 'Offline' : 'Checking...'}</span>
        </div>
      </div>
    </header>
  );
}